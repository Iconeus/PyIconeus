from typing import Union
from .v2.v2 import read_binary
from ..models.Scan import Scan
from ..models.Bps import Bps
from ..models.Roi import Roi
from ..models.Raw import Raw
import struct
import os

global SCAN_4CC_STR
global ROI_4CC_STR
global BPS_4CC_STR
global RAW_4CC_STR
SCAN_4CC_STR = "scan"
ROI_4CC_STR = "bri_"
BPS_4CC_STR = "bps_"
RAW_4CC_STR = "raw_"


def check_fourCC(filepath, str_check) -> bool:
    try:
        with open(filepath, "rb") as f:
            fourCC = ""
            for _ in range(4):
                fourCC += str(struct.unpack("@s", f.read(1))[0], encoding="utf-8")
        return fourCC == str_check
    except:
        return False


def read_scan(filepath) -> Scan:
    return Scan(filepath, check_fourCC(filepath, SCAN_4CC_STR))

def read_bri(filepath) -> Roi:
    # check v1 or v2
    return Roi(filepath, check_fourCC(filepath, ROI_4CC_STR))  # v2

def read_bps(filepath: str) -> Bps:
    return Bps(filepath, check_fourCC(filepath, BPS_4CC_STR))

def read_raw(filepath, fileheader, blockStart:int =1, blockEnd:int =1):
    return Raw(filepath, fileheader, blockStart, blockEnd)

def dispatch_extension(filepath, fileheader, blockStart:int = 1, blockEnd: int = 1) -> Scan | Bps | Roi | None:
    if filepath.endswith(".scan"):
        return read_scan(filepath)
    elif filepath.endswith(".bps"):
        return read_bps(filepath)
    elif filepath.endswith(".bri"):
        return read_bri(filepath)
    elif fileheader and filepath.endswith(".raw") and fileheader.endswith(".hraw"):
        return read_raw(filepath, fileheader, blockStart, blockEnd)
    else:
        return None


def open_path(path: str, path2:str | None = None, blockStart:int = 1, blockEnd: int = 1) -> Union[Scan, Bps, None, FileNotFoundError]:
    try:
        if not os.path.isfile(path):
            raise FileNotFoundError
    except FileNotFoundError as e:
        e.errno = 2
        e.filename = path
        e.strerror = "The following file does not exist"
        raise e
    return dispatch_extension(path, path2, blockStart, blockEnd)  # ty:ignore[invalid-return-type]
