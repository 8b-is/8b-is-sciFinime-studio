#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Report whether the macOS screen is locked.

Prints `1` if the screen is locked, `0` otherwise. Exit status is always 0.
Reads `CGSSessionScreenIsLocked` from the login session via CoreGraphics —
the key is absent (or false) when unlocked, true when locked. No dependencies.
"""

import ctypes
from ctypes import c_void_p, c_char_p, c_bool, c_int32


def is_locked() -> bool:
    cg = ctypes.CDLL(
        "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
    )
    cf = ctypes.CDLL(
        "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
    )
    cg.CGSessionCopyCurrentDictionary.restype = c_void_p
    cf.CFDictionaryGetValue.restype = c_void_p
    cf.CFDictionaryGetValue.argtypes = [c_void_p, c_void_p]
    cf.CFStringCreateWithCString.restype = c_void_p
    cf.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_int32]
    cf.CFBooleanGetValue.restype = c_bool
    cf.CFBooleanGetValue.argtypes = [c_void_p]
    cf.CFGetTypeID.restype = c_void_p
    cf.CFGetTypeID.argtypes = [c_void_p]
    cf.CFBooleanGetTypeID.restype = c_void_p

    session = cg.CGSessionCopyCurrentDictionary()
    key = cf.CFStringCreateWithCString(None, b"CGSSessionScreenIsLocked", 0)
    val = cf.CFDictionaryGetValue(session, key)
    if not val:
        return False
    if cf.CFGetTypeID(val) == cf.CFBooleanGetTypeID():
        return bool(cf.CFBooleanGetValue(val))
    return False


if __name__ == "__main__":
    print(1 if is_locked() else 0)
