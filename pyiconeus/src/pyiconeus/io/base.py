from typing import Union
from src.io.v2.v2 import read_binary
from src.io.bps.bps_reader import read_h5_bps
from src.models.Scan import Scan
from src.models.Bps import Bps
from src.models.Roi import Roi
from src.io.roi.bri_reader import bri_reader_binary, bri_reader_hdf5
import struct
import os

global SCAN_4CC_VALUE
SCAN_4CC_VALUE = 1851876211


def check_fourCC(filepath) -> bool | FileNotFoundError:
    with open(filepath, "rb") as f:
        fourCC = struct.unpack('@L', f.read(4))[0]
    return fourCC == SCAN_4CC_VALUE


def read_scan(filepath) -> Scan | None:
    # check v1 or v2
    if check_fourCC(filepath):  # v2
        scan: Scan = read_binary(filepath)
    else:  # v1
        # TODO
        return None
    return scan


def read_bri(filepath) -> Roi:
    # check v1 or v2
    if check_fourCC(filepath):  # v2
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
    return dispatch_extension(path)
