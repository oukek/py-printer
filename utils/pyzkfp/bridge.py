import argparse
import base64
import json
import sys
import time
import traceback
from typing import Any, Dict, Optional

try:
    from . import ZKFP2
except ImportError:
    from pyzkfp import ZKFP2


def _b64_encode(value: Any) -> str:
    if not isinstance(value, bytes):
        value = bytes(value)
    return base64.b64encode(value).decode("ascii")


def _b64_decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


class FingerprintBridge:
    def __init__(self) -> None:
        self.scanner: Optional[ZKFP2] = None

    def close(self) -> None:
        scanner = self.scanner
        self.scanner = None
        if scanner is not None:
            scanner.Terminate()

    def _require_scanner(self) -> ZKFP2:
        if self.scanner is None:
            raise RuntimeError("Device is not open. Send an `open` command first.")
        return self.scanner

    def _template_from_b64(self, value: str) -> Any:
        scanner = self._require_scanner()
        data = _b64_decode(value)
        array = scanner._sdk["Array"]
        byte = scanner._sdk["Byte"]
        return array[byte](data)

    def _capture(self, timeout_ms: int) -> Dict[str, Any]:
        scanner = self._require_scanner()
        deadline = time.monotonic() + timeout_ms / 1000

        while time.monotonic() <= deadline:
            capture = scanner.AcquireFingerprint()
            if capture:
                template, image = capture
                return {
                    "templateBase64": _b64_encode(template),
                    "imageBase64": _b64_encode(image),
                    "width": scanner.width,
                    "height": scanner.height,
                }
            time.sleep(0.05)

        raise TimeoutError("Timed out waiting for fingerprint capture.")

    def handle(self, command: str, params: Dict[str, Any]) -> Any:
        if command == "ping":
            return {"status": "ok"}

        if command == "device_count":
            if self.scanner is not None:
                return {"count": self.scanner.GetDeviceCount()}

            scanner = None
            try:
                scanner = ZKFP2()
                scanner.Init()
                return {"count": scanner.GetDeviceCount()}
            finally:
                if scanner is not None:
                    try:
                        scanner.Terminate()
                    except Exception:
                        pass

        if command == "open":
            if self.scanner is not None:
                self.close()

            index = int(params.get("index", 0))
            self.scanner = ZKFP2.open(index)
            return {
                "serialNumber": (self.scanner.dev_serial_number or "").rstrip("\x00"),
                "width": self.scanner.width,
                "height": self.scanner.height,
            }

        if command == "close":
            self.close()
            return {"closed": True}

        if command == "capture":
            timeout_ms = int(params.get("timeoutMs", 10000))
            return self._capture(timeout_ms)

        if command == "identify":
            scanner = self._require_scanner()
            template_b64 = params.get("templateBase64")
            if template_b64:
                template = self._template_from_b64(template_b64)
                capture = None
            else:
                capture = self._capture(int(params.get("timeoutMs", 10000)))
                template = self._template_from_b64(capture["templateBase64"])

            fid, score = scanner.DBIdentify(template)
            result = {"fid": fid, "score": score}
            if capture is not None:
                result["capture"] = capture
            return result

        if command == "match":
            scanner = self._require_scanner()
            temp1 = self._template_from_b64(params["template1Base64"])
            temp2 = self._template_from_b64(params["template2Base64"])
            return {"score": scanner.DBMatch(temp1, temp2)}

        if command == "merge_templates":
            scanner = self._require_scanner()
            templates = params["templatesBase64"]
            if len(templates) != 3:
                raise ValueError("ZKFP2 template merge requires exactly 3 fingerprint samples.")

            temp1 = self._template_from_b64(templates[0])
            temp2 = self._template_from_b64(templates[1])
            temp3 = self._template_from_b64(templates[2])
            reg_template, reg_template_len = scanner.DBMerge(temp1, temp2, temp3)

            fid = params.get("fid")
            if fid is not None:
                scanner.DBAdd(int(fid), reg_template)

            return {
                "fid": int(fid) if fid is not None else None,
                "templateBase64": _b64_encode(reg_template),
                "templateLength": reg_template_len,
            }

        if command == "enroll":
            scanner = self._require_scanner()
            sample_count = int(params.get("sampleCount", 3))
            timeout_ms = int(params.get("timeoutMs", 10000))
            fid = params.get("fid")

            if sample_count != 3:
                raise ValueError("ZKFP2 enrollment requires exactly 3 fingerprint samples.")

            captures = []
            templates = []
            for index in range(sample_count):
                capture = self._capture(timeout_ms)
                template = self._template_from_b64(capture["templateBase64"])
                if templates and scanner.DBMatch(templates[-1], template) <= 0:
                    raise RuntimeError("Different finger detected during enrollment.")

                captures.append(capture)
                templates.append(template)

            reg_template, reg_template_len = scanner.DBMerge(*templates)
            if fid is not None:
                scanner.DBAdd(int(fid), reg_template)

            return {
                "fid": int(fid) if fid is not None else None,
                "templateBase64": _b64_encode(reg_template),
                "templateLength": reg_template_len,
                "captures": captures,
            }

        if command == "add_template":
            scanner = self._require_scanner()
            fid = int(params["fid"])
            template = self._template_from_b64(params["templateBase64"])
            scanner.DBAdd(fid, template)
            return {"added": True, "fid": fid}

        if command == "delete_template":
            scanner = self._require_scanner()
            fid = int(params["fid"])
            scanner.DBDel(fid)
            return {"deleted": True, "fid": fid}

        if command == "clear_templates":
            self._require_scanner().DBClear()
            return {"cleared": True}

        if command == "light":
            color = params.get("color", "green")
            duration = float(params.get("duration", 0.5))
            self._require_scanner().Light(color, duration)
            return {"color": color, "duration": duration}

        if command == "shutdown":
            self.close()
            return {"shutdown": True}

        raise ValueError(f"Unknown command: {command}")


def _response(message_id: Any, ok: bool, payload: Any = None) -> str:
    response = {"id": message_id, "ok": ok}
    if ok:
        response["result"] = payload
    else:
        response["error"] = payload
    return json.dumps(response, ensure_ascii=True)


def serve(debug: bool = False) -> int:
    bridge = FingerprintBridge()

    try:
        for line in sys.stdin:
            line = line.strip().lstrip("\ufeff")
            if not line:
                continue

            request: Dict[str, Any] = {}
            try:
                request = json.loads(line)
                message_id = request.get("id")
                command = request["command"]
                params = request.get("params") or {}
                result = bridge.handle(command, params)
                print(_response(message_id, True, result), flush=True)

                if command == "shutdown":
                    return 0
            except Exception as exc:
                error = {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                }
                if debug:
                    error["traceback"] = traceback.format_exc()
                print(_response(request.get("id"), False, error), flush=True)
    finally:
        try:
            bridge.close()
        except Exception:
            pass

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="ZKFP2 JSON-lines bridge for Electron.")
    parser.add_argument("--stdio", action="store_true", help="Run the JSON-lines stdio service.")
    parser.add_argument("--debug", action="store_true", help="Include tracebacks in error responses.")
    args = parser.parse_args()

    if args.stdio:
        return serve(debug=args.debug)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
