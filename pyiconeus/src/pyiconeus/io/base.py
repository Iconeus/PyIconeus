from typing import Union
from .v2.v2 import read_binary
from ..io.bps.bps_reader import read_h5_bps
from ..models.Scan import Scan
from ..models.Bps import Bps
from ..models.Roi import Roi
from ..io.roi.bri_reader import bri_reader_binary, bri_reader_hdf5
import struct
import os

global SCAN_4CC_STR
global ROI_4CC_STR
SCAN_4CC_STR = 'scan'
ROI_4CC_STR = 'bri_'


def check_fourCC(filepath, str_check) -> bool | FileNotFoundError:
    try:
        with open(filepath, "rb") as f:
            fourCC = ""
            for _ in range(4):
                fourCC += str(struct.unpack('@s', f.read(1))[0], encoding='utf-8')
                print(fourCC)
        return fourCC == str_check
    except:
        return False


def read_scan(filepath) -> Scan | None:
    # check v1 or v2
    if check_fourCC(filepath, SCAN_4CC_STR):  # v2
        scan: Scan = read_binary(filepath)
    else:  # v1
        # TODO
        return None
    return scan


def read_bri(filepath) -> Roi:
    # check v1 or v2
    if check_fourCC(filepath,ROI_4CC_STR):  # v2
        print(filepath)
        roi: Roi = bri_reader_binary(filepath)
    else:  # v1
        roi: Roi = bri_reader_hdf5(filepath)
    return roi

def read_bps(filepath: str) -> Bps | None:
    return read_h5_bps(filepath)


def dispatch_extension(filepath) -> Scan | Bps | Roi | None:
    if filepath.endswith(".scan"):
        return read_scan(filepath)
    elif filepath.endswith(".bps"):
        return read_bps(filepath)
    elif filepath.endswith(".bri"):
        return read_bri(filepath)
    elif filepath.endswith(".raw") or filepath.endswith(".hraw"):
        return None  # TODO implement RawIQ reader
    else:
        return None


def open_path(path: str) -> Union[Scan, Bps, None, FileNotFoundError]:
    try:
        if not os.path.isfile(path):
            raise FileNotFoundError
    except FileNotFoundError as e:
        e.errno = 2
        e.filename = path
        e.strerror = "The following file does not exist"
        raise e
    return dispatch_extension(path)  # ty:ignore[invalid-return-type]
