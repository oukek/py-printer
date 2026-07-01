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
import subprocess
import sys
from typing import Any, Dict, Iterator, Optional

from .pyzkfp.bridge import FingerprintBridge, _b64_encode
from .pyzkfp.zkfp2 import ZKFP2, _dll_path


def _installer_path() -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "pyzkfp", "setup.exe")
    package_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(package_dir, "pyzkfp", "setup.exe")


def _module_available(module_name: str) -> bool:
    module = sys.modules.get(module_name)
    if module is not None:
        return True

    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        # pythonnet 的 clr 模块在某些场景下已加载但 __spec__ 为 None，
        # 这时 find_spec() 会抛 ValueError，不应让诊断接口直接 500。
        return module_name in sys.modules


def _shell_execute_error_details(code: int) -> Dict[str, str]:
    error_map = {
        0: {
            "type": "ShellExecuteError",
            "message": "Windows 无法启动安装程序，系统资源可能不足。",
            "hint": "请关闭部分程序后重试，或直接手动运行 setup.exe。",
        },
        2: {
            "type": "FileNotFoundError",
            "message": "未找到 setup.exe 安装程序文件。",
            "hint": "请确认安装包已完整打包，或检查 setup.exe 是否被杀毒软件隔离。",
        },
        3: {
            "type": "PathNotFoundError",
            "message": "安装程序所在路径不存在。",
            "hint": "请检查程序解压目录是否完整，或重新安装当前应用。",
        },
        5: {
            "type": "AccessDeniedError",
            "message": "没有权限启动安装程序，可能被系统策略阻止，或用户取消了 UAC 授权。",
            "hint": "请以管理员身份运行当前程序，或手动右键以管理员身份运行 setup.exe。",
        },
        8: {
            "type": "OutOfMemoryError",
            "message": "系统内存不足，无法启动安装程序。",
            "hint": "请释放内存后重试。",
        },
        26: {
            "type": "ShareError",
            "message": "无法共享访问安装程序文件。",
            "hint": "请确认 setup.exe 未被其他进程占用。",
        },
        27: {
            "type": "AssociationIncompleteError",
            "message": "安装程序的文件关联信息不完整，无法执行。",
            "hint": "请尝试手动运行 setup.exe，或重新安装当前应用。",
        },
        28: {
            "type": "DDETimeoutError",
            "message": "启动安装程序时等待系统响应超时。",
            "hint": "请稍后重试，或手动运行 setup.exe。",
        },
        29: {
            "type": "DDEFailureError",
            "message": "Windows 在启动安装程序时发生通信错误。",
            "hint": "请稍后重试，或手动运行 setup.exe。",
        },
        30: {
            "type": "DDEBusyError",
            "message": "Windows 正忙，暂时无法启动安装程序。",
            "hint": "请稍后重试。",
        },
        31: {
            "type": "NoAssociationError",
            "message": "系统无法识别 setup.exe 的执行方式。",
            "hint": "请检查系统环境，或手动双击运行 setup.exe。",
        },
        32: {
            "type": "DllNotFoundError",
            "message": "启动安装程序所需的系统组件缺失。",
            "hint": "请检查系统运行库是否完整，或换一台机器验证。",
        },
    }
    return error_map.get(code, {
        "type": "ShellExecuteError",
        "message": f"Windows 启动安装程序失败，ShellExecuteW 返回码: {code}",
        "hint": "请检查系统权限、UAC 授权窗口和 setup.exe 文件状态。",
    })


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

    @staticmethod
    def _failure_result(
        error: str,
        message: str,
        error_type: str = "RuntimeError",
        result: Optional[Dict[str, Any]] = None,
        hint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        response = {
            "success": False,
            "error": error,
            "message": message,
            "type": error_type,
        }
        if result is not None:
            response["result"] = result
        if hint:
            response["hint"] = hint
        if details:
            response["details"] = details
        return response

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
        setup_path = _installer_path()
        dll_path = os.path.join(dll_dir, "libzkfpcsharp.dll")

        result = {
            "pythonnetAvailable": _module_available("pythonnet"),
            "clrAvailable": _module_available("clr"),
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

    def run_installer(self, elevated: bool = True) -> Dict[str, Any]:
        """Launch the bundled ZKFP installer."""
        setup_path = _installer_path()
        if not os.path.exists(setup_path):
            return self._failure_result(
                "未找到指纹安装程序",
                f"setup.exe 不存在: {setup_path}",
                error_type="FileNotFoundError",
                hint="请确认 setup.exe 已随程序一起发布，或检查文件是否被安全软件移除。",
                details={
                    "installerPath": setup_path,
                    "elevated": elevated,
                },
            )

        try:
            if os.name == "nt" and elevated:
                import ctypes
                result = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    setup_path,
                    "",
                    None,
                    1,
                )
                if result <= 32:
                    error_details = _shell_execute_error_details(int(result))
                    return self._failure_result(
                        "启动指纹安装程序失败",
                        error_details["message"],
                        error_type=error_details["type"],
                        hint=error_details["hint"],
                        details={
                            "shellExecuteCode": int(result),
                            "installerPath": setup_path,
                            "elevated": True,
                        },
                    )
                return self._success({
                    "started": True,
                    "elevated": True,
                    "installerPath": setup_path,
                }, "指纹安装程序已启动")

            process = subprocess.Popen([setup_path], shell=False)
            return self._success({
                "started": True,
                "elevated": False,
                "pid": process.pid,
                "installerPath": setup_path,
            }, "指纹安装程序已启动")
        except FileNotFoundError:
            return self._failure_result(
                "启动指纹安装程序失败",
                f"未找到 setup.exe: {setup_path}",
                error_type="FileNotFoundError",
                hint="请确认安装程序文件存在，且未被安全软件隔离。",
                details={
                    "installerPath": setup_path,
                    "elevated": elevated,
                },
            )
        except PermissionError as exc:
            return self._failure_result(
                "启动指纹安装程序失败",
                f"没有权限启动 setup.exe: {exc}",
                error_type="PermissionError",
                hint="请尝试以管理员身份运行当前程序，或手动右键以管理员身份运行 setup.exe。",
                details={
                    "installerPath": setup_path,
                    "elevated": elevated,
                },
            )
        except OSError as exc:
            return self._failure_result(
                "启动指纹安装程序失败",
                f"操作系统无法启动 setup.exe: {exc}",
                error_type=exc.__class__.__name__,
                hint="请检查 setup.exe 是否可执行，以及系统环境是否允许启动外部安装程序。",
                details={
                    "installerPath": setup_path,
                    "elevated": elevated,
                },
            )
        except Exception as exc:
            return self._failure("启动指纹安装程序失败", exc)

    def ensure_runtime(self, elevated: bool = True) -> Dict[str, Any]:
        """Run diagnostics and launch the installer only when the SDK is unavailable."""
        diagnostics = self.diagnostics()
        diagnostic_result = diagnostics.get("result") or {}

        if diagnostic_result.get("sdkAvailable"):
            return self._success({
                "ready": True,
                "installStarted": False,
                "diagnostics": diagnostic_result,
            }, "指纹环境可用，无需安装")

        if not diagnostic_result.get("installerExists"):
            return self._failure_result(
                "未找到指纹安装程序",
                "指纹环境不可用，且未找到内置 setup.exe。",
                error_type="FileNotFoundError",
                result={
                    "ready": False,
                    "installStarted": False,
                    "diagnostics": diagnostic_result,
                },
                hint="请确认打包目录完整，或重新安装当前应用。",
            )

        install_result = self.run_installer(elevated=elevated)
        if not install_result.get("success"):
            return {
                **install_result,
                "result": {
                    "ready": False,
                    "installStarted": False,
                    "diagnostics": diagnostic_result,
                    "installer": install_result,
                },
            }
        return self._success({
            "ready": False,
            "installStarted": bool(install_result.get("success")),
            "diagnostics": diagnostic_result,
            "installer": install_result,
        }, "指纹环境不可用，已尝试启动安装程序")

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
