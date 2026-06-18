#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fingerprint service wrapper.

The ZKFP device is stateful and generally exclusive, so this module keeps one
bridge instance and serializes access to it for HTTP requests.
"""

import threading
import importlib.util
import os
from typing import Any, Dict, Iterator, Optional

from .pyzkfp.bridge import FingerprintBridge, _b64_encode
from .pyzkfp.zkfp2 import ZKFP2, _dll_path


class FingerprintService:
    """Thread-safe wrapper around the pyzkfp bridge."""

    def __init__(self) -> None:
        self._bridge = FingerprintBridge()
        self._lock = threading.RLock()

    @staticmethod
    def _success(result: Any = None, message: str = "操作成功") -> Dict[str, Any]:
        response = {
            "success": True,
            "message": message,
        }
        if result is not None:
            response["result"] = result
        return response

    @staticmethod
    def _failure(error: str, exc: Exception) -> Dict[str, Any]:
        return {
            "success": False,
            "error": error,
            "message": str(exc),
            "type": exc.__class__.__name__,
        }

    def call(self, command: str, params: Optional[Dict[str, Any]] = None, message: str = "操作成功") -> Dict[str, Any]:
        """Execute one bridge command with a serialized device lock."""
        try:
            with self._lock:
                result = self._bridge.handle(command, params or {})
            return self._success(result, message)
        except Exception as exc:
            return self._failure("指纹模块操作失败", exc)

    def status(self) -> Dict[str, Any]:
        """Return the local service view of the fingerprint device state."""
        scanner = self._bridge.scanner
        result = {"opened": scanner is not None}
        if scanner is not None:
            result.update({
                "serialNumber": (scanner.dev_serial_number or "").rstrip("\x00"),
                "width": scanner.width,
                "height": scanner.height,
            })
        return self._success(result, "获取指纹设备状态成功")

    def diagnostics(self) -> Dict[str, Any]:
        """Check whether the fingerprint SDK runtime appears usable."""
        dll_dir = _dll_path()
        package_dir = os.path.dirname(os.path.realpath(__file__))
        setup_path = os.path.join(package_dir, "pyzkfp", "setup.exe")
        dll_path = os.path.join(dll_dir, "libzkfpcsharp.dll")

        result = {
            "pythonnetAvailable": importlib.util.find_spec("pythonnet") is not None,
            "clrAvailable": importlib.util.find_spec("clr") is not None,
            "sdkDllExists": os.path.exists(dll_path),
            "sdkDllPath": dll_path,
            "installerExists": os.path.exists(setup_path),
            "installerPath": setup_path,
            "sdkAvailable": False,
            "deviceCount": None,
            "opened": self._bridge.scanner is not None,
        }

        if not result["pythonnetAvailable"]:
            result["error"] = {
                "type": "MissingDependency",
                "message": "pythonnet 未安装，无法加载 ZKFP SDK。",
            }
            return self._success(result, "获取指纹环境检测结果成功")

        if not result["sdkDllExists"]:
            result["error"] = {
                "type": "MissingDll",
                "message": "未找到 libzkfpcsharp.dll，无法加载 ZKFP SDK。",
            }
            return self._success(result, "获取指纹环境检测结果成功")

        scanner = None
        try:
            with self._lock:
                if self._bridge.scanner is not None:
                    result["deviceCount"] = self._bridge.scanner.GetDeviceCount()
                else:
                    scanner = ZKFP2()
                    scanner.Init()
                    result["deviceCount"] = scanner.GetDeviceCount()

            result["sdkAvailable"] = True
        except Exception as exc:
            result["error"] = {
                "type": exc.__class__.__name__,
                "message": str(exc),
                "hint": "如果这里失败，通常表示 ZKFinger 驱动/运行环境未安装，或设备 SDK 依赖不可用。请先安装指纹目录中的 setup.exe。",
            }
        finally:
            if scanner is not None:
                try:
                    scanner.Terminate()
                except Exception:
                    pass

        return self._success(result, "获取指纹环境检测结果成功")

    def load_templates(self, templates, clear_existing: bool = False) -> Dict[str, Any]:
        """Load business-owned templates into the SDK in-memory database."""
        try:
            with self._lock:
                scanner = self._bridge._require_scanner()
                if clear_existing:
                    scanner.DBClear()

                loaded = []
                failed = []
                for index, item in enumerate(templates):
                    try:
                        fid = int(item["fid"])
                        template_base64 = item.get("templateBase64") or item.get("template_base64")
                        if not template_base64:
                            raise ValueError("templateBase64 is required")

                        template = self._bridge._template_from_b64(template_base64)
                        scanner.DBAdd(fid, template)
                        loaded.append(fid)
                    except Exception as exc:
                        failed.append({
                            "index": index,
                            "fid": item.get("fid") if isinstance(item, dict) else None,
                            "message": str(exc),
                            "type": exc.__class__.__name__,
                        })

            return self._success({
                "loaded": loaded,
                "loadedCount": len(loaded),
                "failed": failed,
                "failedCount": len(failed),
                "clearExisting": clear_existing,
            }, "指纹模板批量加载完成")
        except Exception as exc:
            return self._failure("批量加载指纹模板失败", exc)

    def close(self) -> Dict[str, Any]:
        """Close the currently opened device."""
        try:
            with self._lock:
                self._bridge.close()
            return self._success({"closed": True}, "指纹设备已关闭")
        except Exception as exc:
            return self._failure("关闭指纹设备失败", exc)

    def enroll_events(
        self,
        fid: Optional[int] = None,
        sample_count: int = 3,
        timeout_ms: int = 10000,
    ) -> Iterator[Dict[str, Any]]:
        """Yield enrollment progress events as each fingerprint sample is captured."""
        with self._lock:
            scanner = self._bridge._require_scanner()

            if sample_count != 3:
                raise ValueError("ZKFP2 enrollment requires exactly 3 fingerprint samples.")

            captures = []
            templates = []

            for index in range(sample_count):
                capture = self._bridge._capture(timeout_ms)
                template = self._bridge._template_from_b64(capture["templateBase64"])

                if templates and scanner.DBMatch(templates[-1], template) <= 0:
                    raise RuntimeError("Different finger detected during enrollment.")

                captures.append(capture)
                templates.append(template)

                yield {
                    "step": index + 1,
                    "total": sample_count,
                    "capture": capture,
                }

            reg_template, reg_template_len = scanner.DBMerge(*templates)
            if fid is not None:
                scanner.DBAdd(int(fid), reg_template)

            yield {
                "fid": int(fid) if fid is not None else None,
                "templateBase64": _b64_encode(reg_template),
                "templateLength": reg_template_len,
                "captures": captures,
            }


fingerprint_service = FingerprintService()
