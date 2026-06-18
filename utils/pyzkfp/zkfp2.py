from threading import Thread
from time import sleep
from typing import Any, Dict, Optional, Tuple
import importlib
import os
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))


def _dll_path() -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "pyzkfp", "dll")
    return os.path.join(dir_path, "dll")

try:
    from ._construct.errors_handler import *
except ImportError:
    from pyzkfp._construct.errors_handler import *

try:
    from PIL import Image
except ImportError:
    Image = None

from io import BytesIO
from base64 import b64encode

_sdk: Optional[Dict[str, Any]] = None


def _load_sdk() -> Dict[str, Any]:
    global _sdk

    if _sdk is not None:
        return _sdk

    dll_path = _dll_path()
    if dll_path not in sys.path:
        sys.path.append(dll_path)

    try:
        import clr
    except ImportError as exc:
        raise RuntimeError(
            "pythonnet is required to use ZKFP2. Install it with `pip install pythonnet` "
            "and make sure a compatible .NET or Mono runtime is available."
        ) from exc

    try:
        clr.AddReference("libzkfpcsharp")
        clr.AddReference("System")
        system = importlib.import_module("System")
        libzkfpcsharp = importlib.import_module("libzkfpcsharp")
    except Exception as exc:
        raise RuntimeError(
            "Failed to load libzkfpcsharp.dll. Install the ZKFinger SDK and make sure "
            "the native runtime dependencies are available."
        ) from exc

    _sdk = {
        "Array": system.Array,
        "Byte": system.Byte,
        "IntPtr": system.IntPtr,
        "zkfp": libzkfpcsharp.zkfp,
        "zkfp2": libzkfpcsharp.zkfp2,
    }
    return _sdk


def _require_image():
    if Image is None:
        raise ImportError("Pillow is required for image conversion helpers.")
    return Image


class ZKFP2:
    """
    Python wrapper for ZKFinger Reader SDK.
    """

    def __init__(self):
        """
        Initialize the ZKFP2 class and load the DLL.
        """
        self._sdk = _load_sdk()
        self.zkfp2 = self._sdk["zkfp2"]()
        self._zkfp = self._sdk["zkfp"]()
        self.devHandle: Optional[int] = None
        self.dbHandle: Optional[int] = None

        self.dev_serial_number: Optional[str] = None

        self.width: Optional[int] = None
        self.height: Optional[int] = None
        self._zkfp_initialized = False


    def _handle_error(self, err_code) -> None:
        error_mapping = {
            -25: (DeviceAlreadyConnectedError, "The device is already connected"),
            -24: (DeviceNotInitializedError, "The device is not initialized"),
            -23: (DeviceNotStartedError, "The device is not started"),
            -22: (FailedToCombineTemplatesError, "Failed to combine the registered fingerprint templates"),
            -20: (FingerprintComparisonFailedError, "Fingerprint comparison failed"),
            -18: (CaptureCancelledError, "Capture cancelled"),
            -17: (OperationFailedError, "Operation failed"),
            -14: (FailedToDeleteTemplateError, "Failed to delete the fingerprint template"),
            -13: (FailedToAddTemplateError, "Failed to add the fingerprint template"),
            -12: (FingerprintCapturedError, "The fingerprint is being captured"),
            -11: (InsufficientMemoryError, "Insufficient memory"),
            -10: (AbortedError, "Aborted"),
            -9: (FailedToExtractTemplateError, "Failed to extract the fingerprint template"),
            -8: (FailedToCaptureImageError, "Failed to capture the image"),
            -7: (InvalidHandleError, "Invalid Handle"),
            -6: (FailedToStartDeviceError, "Failed to start the device"),
            -5: (InvalidParameterError, "Invalid parameter"),
            -4: (NotSupportedError, "Not supported by the interface"),
            -3: (NoDeviceConnectedError, "No device connected"),
            -2: (CaptureLibraryInitializationError, "Failed to initialize the capture library"),
            -1: (AlgorithmLibraryInitializationError, "Failed to initialize the algorithm library"),
        }

        if err_code in error_mapping:
            error_class, error_message = error_mapping[err_code]
            raise error_class(error_message)

        if isinstance(err_code, int) and err_code < 0:
            raise UnknownError(f"Unknown ZKFP2 error code: {err_code}")


    def _is_zero_handle(self, handle: Any) -> bool:
        if handle is None:
            return True

        try:
            return handle == self._sdk["IntPtr"].Zero
        except Exception:
            return False


    def _handle_handle_error(self, handle: Any, message: str) -> None:
        if self._is_zero_handle(handle):
            raise OperationFailedError(message)


    def _require_device(self) -> None:
        if self._is_zero_handle(self.devHandle):
            raise DeviceNotInitializedError("Device not initialized.")


    def _require_cache(self) -> None:
        if self._is_zero_handle(self.dbHandle):
            raise DeviceNotInitializedError("Cache not initialized.")


    def _require_capture_parameters(self) -> None:
        if self.width is None or self.height is None:
            raise DeviceNotInitializedError("Capture parameters not initialized.")


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc, traceback):
        self.Terminate()
        return False


    @classmethod
    def open(cls, index: int = 0):
        scanner = cls()
        scanner.Init()
        scanner.OpenDevice(index)
        return scanner


    def Init(self) -> None:
        """
        Initialize the device.
        """
        ret = self.zkfp2.Init()
        self._handle_error(ret)


    def Terminate(self) -> None:
        """
        Release library resources.
        """
        if not self._is_zero_handle(self.dbHandle):
            self.DBFree()

        if not self._is_zero_handle(self.devHandle):
            self.CloseDevice()

        if self._zkfp_initialized:
            ret = self._zkfp.Finalize()
            self._handle_error(ret)
            self._zkfp_initialized = False

        ret = self.zkfp2.Terminate()
        self._handle_error(ret)


    def GetDeviceCount(self) -> int:
        """
        Acquire the number of connected devices.

        Returns:
            int: The device count.
        """
        return self.zkfp2.GetDeviceCount()


    def OpenDevice(self, index: int = 0) -> int:
        """
        Connect to a device.

        Args:
            `index` (int): Device index.

        Returns:
            `devHandle`: Device handle.
        """
        devHandle = self.zkfp2.OpenDevice(index)
        self._handle_handle_error(devHandle, "OpenDevice failed.")
        self.devHandle = devHandle

        try:
            # Get device serial number and image width and height
            ret = self._zkfp.Initialize()
            self._handle_error(ret)
            self._zkfp_initialized = True

            ret = self._zkfp.OpenDevice(index)
            self._handle_error(ret)

            self.dev_serial_number = self._zkfp.devSn
            self.width  = self._zkfp.imageWidth
            self.height = self._zkfp.imageHeight

            self.DBInit()
        except Exception:
            self._cleanup_open_device()
            raise

        return self.devHandle


    def _cleanup_open_device(self) -> None:
        if not self._is_zero_handle(self.dbHandle):
            try:
                self.zkfp2.DBFree(self.dbHandle)
            except Exception:
                pass
            self.dbHandle = None

        if not self._is_zero_handle(self.devHandle):
            try:
                self.zkfp2.CloseDevice(self.devHandle)
            except Exception:
                pass
            self.devHandle = None

        if self._zkfp_initialized:
            try:
                self._zkfp.CloseDevice()
            except Exception:
                pass
            try:
                self._zkfp.Finalize()
            except Exception:
                pass
            self._zkfp_initialized = False

        self.dev_serial_number = None
        self.width = None
        self.height = None


    def CloseDevice(self) -> None:
        """
        Shut down a device.
        """
        self._require_device()

        if self.dbHandle is not None:
            self.DBFree()

        ret = self.zkfp2.CloseDevice(self.devHandle)
        self._handle_error(ret)

        ret = self._zkfp.CloseDevice()
        self._handle_error(ret)

        if self._zkfp_initialized:
            ret = self._zkfp.Finalize()
            self._handle_error(ret)
            self._zkfp_initialized = False

        self.devHandle = None
        self.dev_serial_number = None
        self.width = None
        self.height = None


    def SetParameters(self, code: int, paramValue: Any = bytes([1, 0, 0, 0]), size: int = 4) -> Any:
        """
        Set a parameter.

        Args:
            `code` (int): Parameter code.
            `paramValue` (bytes): Parameter value.
            `size` (int): Parameter data length.
        """
        self._require_device()
        
        ret = self._zkfp.SetParameters(code, paramValue, size)
        self._handle_error(ret)
        return paramValue


    def GetParameters(self, code: int) -> Any:
        """
        Acquire a parameter.

        Args:
            `code` (int): Parameter code.

        Returns:
            int: `paramValue` if succeeded.
        """
        self._require_device()

        paramValue = self.Int2ByteArray(0)
        ret, size = self._zkfp.GetParameters(code, paramValue, 4)
        self._handle_error(ret)
        return paramValue


    def AcquireFingerprint(self) -> Optional[Tuple[Any, bytes]]:
        """
        Capture a fingerprint image and template.

        Args:
            `size` (int): Template array length.

        Returns:
            if result == 0:
                bytes: Template data.
                bytes: Image data.
            else: None.
        """
        self._require_device()
        self._require_capture_parameters()

        Array = self._sdk["Array"]
        Byte = self._sdk["Byte"]
        imgBuffer = Array[Byte](self.width * self.height)
        template = Array[Byte](1024*2)  
        size = template.Length

        ret, size = self.zkfp2.AcquireFingerprint(self.devHandle, imgBuffer, template, size)
        if ret == 0: # only return when ther is a fingerprint captured
            return template, bytes(imgBuffer)

        if ret != -8: 
            self._handle_error(ret) # something went wrong => raise error


    def AcquireFingerprintImage(self) -> Optional[bytes]:
        """
        Capture a fingerprint image.

        Args:
            imgBuffer (bytes): Returned image.
        
        Returns:
            bytes: Image data.
        """
        self._require_device()
        self._require_capture_parameters()

        Array = self._sdk["Array"]
        Byte = self._sdk["Byte"]
        imgBuffer = Array[Byte](self.width * self.height)

        ret = self.zkfp2.AcquireFingerprintImage(self.devHandle, imgBuffer)

        if ret == 0: # only return when there is a fingerprint captured
            return bytes(imgBuffer)

        if ret != -8: 
            self._handle_error(ret) # something went wrong => raise error


    def DBInit(self) -> int:
        """
        Create an algorithm cache.

        Returns:
            dbHandle: CacheDB handle.
        """
        dbHandle = self.zkfp2.DBInit()
        self._handle_handle_error(dbHandle, "DBInit failed.")
        self.dbHandle = dbHandle
        return self.dbHandle


    def DBFree(self) -> None:
        """
        Release an algorithm cache.
        """
        self._require_cache()

        ret = self.zkfp2.DBFree(self.dbHandle)
        self._handle_error(ret)
        self.dbHandle = None


    def DBMerge(self, temp1: Any, temp2: Any, temp3: Any) -> Tuple[Any, int]:
        """
        Combine three pre-registered fingerprint templates as one registered fingerprint template.

        Args:
            temp1 (bytes): Pre-registered fingerprint template 1.
            temp2 (bytes): Pre-registered fingerprint template 2.
            temp3 (bytes): Pre-registered fingerprint template 3.
        
        Returns:
            regTemp (bytes): Returned registered template.
            regTempLen (int): Template array length.
        """
        self._require_cache()

        Array = self._sdk["Array"]
        Byte = self._sdk["Byte"]
        regTemp = Array[Byte](1024*2)
        regTempLen = len(regTemp)
        ret = self.zkfp2.DBMerge(self.dbHandle, temp1, temp2, temp3, regTemp, regTempLen)
        self._handle_error(ret)
        return regTemp, regTempLen


    def DBAdd(self, fid: int, regTemp: bytes) -> None:
        """
        Add a registered template to the memory.

        Args:
            fid (int): Fingerprint ID.
            regTemp (bytes): Registered template.
        """
        self._require_cache()

        ret = self.zkfp2.DBAdd(self.dbHandle, fid, regTemp)
        self._handle_error(ret)


    def DBDel(self, fid: int) -> None:
        """
        Delete a registered fingerprint template from the memory.

        Args:
            fid (int): Fingerprint ID.
        """
        self._require_cache()

        ret = self.zkfp2.DBDel(self.dbHandle, fid)
        self._handle_error(ret)


    def DBClear(self) -> None:
        """
        Clear all fingerprint templates in the memory.
        """
        self._require_cache()

        ret = self.zkfp2.DBClear(self.dbHandle)
        self._handle_error(ret)


    def DBIdentify(self, temp: bytes) -> Tuple[int, int]:
        """
        Conduct 1:N comparison.

        Args:
            temp (bytes): Template used for comparison.
        
        Returns:
            fid (int): Fingerprint ID if succeeded.
            score (int): Comparison score if succeeded.
        """
        self._require_cache()

        fid = 0
        score = 0

        ret, fid, score = self.zkfp2.DBIdentify(self.dbHandle, temp, fid, score)
        if ret not in [0, -17]:
            self._handle_error(ret)
        return fid, score


    def DBMatch(self, temp1: bytes, temp2: bytes) -> int:
        """
        Conduct 1:1 comparison on two fingerprint templates.

        Args:
            temp1 (bytes): Template 1 used for comparison.
            temp2 (bytes): Template 2 used for comparison.

        Returns:
            int: Comparison score if succeeded.
        """
        self._require_cache()

        score_result = self.zkfp2.DBMatch(self.dbHandle, temp1, temp2)
        
        if score_result < 0: self._handle_error(score_result)
        
        return score_result


    def Blob2Base64String(self, buf: bytes) -> str:
        """
        Convert a byte[] array into a Base64 string.

        Args:
            buf (bytes): BLOB data.
            len (int): Length.

        Returns:
            str: Base64 string.
        """
        # the sdk's function wasn't really working for me, so i made my own with PIL

        # SKD's function:
        # strBase64 = String.Empty

        # ret, result = zkfp.Blob2Base64String(buf, len(buf) if isinstance(buf, bytes) else buf.Length, strBase64)
        # self._handle_error(ret)
        # return result

        # my function
        if not isinstance(buf, bytes):
            buf = bytes(buf)

        self._require_capture_parameters()
        image_cls = _require_image()
        bf = BytesIO()
        image = image_cls.frombytes("L", (self.width, self.height), buf)
        image.save(bf, format="PNG")
        return b64encode(bf.getvalue()).decode("utf-8")


    def Base64String2Blob(self, strBase64: str) -> bytes:
        """
        Convert a Base64 string into a byte[] array.

        Args:
            strBase64 (str): Base64 string.

        Returns:
            bytes: the `blob` Byte[] array.
        """

        converter = getattr(self.zkfp2, "Base64String2Blob", None)
        if converter is None:
            converter = getattr(self.zkfp2, "Base64ToBlob")

        blob = converter(strBase64)
        return blob


    def ByteArray2Int(self, buf: bytes) -> int:
        """
        Convert a 4-byte array into an integer.

        Args:
            buf (bytes): Byte array.

        Returns:
            int: Converted integer if succeeded, None otherwise.
        """
        str_len, value = self.zkfp2.ByteArray2Int(buf, 0)
        return value


    def Int2ByteArray(self, value: int) -> Any:
        """
        Convert an integer into a 4-byte array.

        Args:
            value (int): Data.

        Returns:
            bytes: Byte array.
        """
        Array = self._sdk["Array"]
        Byte = self._sdk["Byte"]
        buf = Array[Byte](4)
        result = self.zkfp2.Int2ByteArray(value, buf)
        if not result:
            raise OperationFailedError("Failed to convert integer to byte array.")
        return buf


    def ExtractFromImage(self, FileName: str, DPI: int) -> Any:
        """
        Extract a template from a BMP or JPG file.

        Args:
            FileName (str): Full path of a file.
            DPI (int): Image DPI.
        """
        self._require_cache()

        Array = self._sdk["Array"]
        Byte = self._sdk["Byte"]
        template = Array[Byte](1024*2)
        size = template.Length
        ret = self.zkfp2.ExtractFromImage(self.dbHandle, FileName, DPI, template, size)
        self._handle_error(ret)
        return template


    def Light(self, color: str, duration: float = 0.5) -> Thread:
        colors_translation = {"white": 101, "green": 102, "red": 103}
        if color not in colors_translation:
            raise ValueError(f"Invalid color: {color}")

        def light_thread():
            self.SetParameters(colors_translation[color])
            sleep(duration)
            self.SetParameters(colors_translation[color], self.Int2ByteArray(0)) 

            # !NOTE: for some reason, the light doesn't turn off when set to 0.
            # I haven't tested it on other devices besides the SLK20R. 
            # If you think you have a solution/addition to this part of the code, please open a PR.

        thread = Thread(target=light_thread, daemon=True)
        thread.start()
        return thread

    
    def show_image(self, img: bytes):
        """
        Show an image.

        Args:
            img (bytes): Image data.
        """
        if not isinstance(img, bytes):
            img = bytes(img)

        self._require_capture_parameters()
        image_cls = _require_image()
        image = image_cls.frombytes("L", (self.width, self.height), img)
        image.show()
