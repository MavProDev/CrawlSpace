import ctypes
import ctypes.wintypes

_mutex_handle = None

def acquire_lock() -> bool:
    """Acquire a Windows named mutex. Returns True if this is the first instance."""
    global _mutex_handle
    _mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, True, "CrawlSpace_SingleInstance_Mutex")
    last_error = ctypes.windll.kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183
    if last_error == ERROR_ALREADY_EXISTS:
        ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        _mutex_handle = None
        return False
    return True

def release_lock():
    """Release the named mutex."""
    global _mutex_handle
    if _mutex_handle:
        ctypes.windll.kernel32.ReleaseMutex(_mutex_handle)
        ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        _mutex_handle = None
