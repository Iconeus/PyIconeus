import os
from typing import Union

from ..models.Bps import Bps
from ..models.Raw import Raw
from ..models.Roi import Roi
from ..models.Scan import Scan

SCAN_4CC_STR = "scan"
ROI_4CC_STR = "bri_"
BPS_4CC_STR = "bps_"
RAW_4CC_STR = "raw_"


def check_fourCC(filepath: str, str_check: str) -> bool:
    """Check whether a file's leading 4-byte magic number matches str_check."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(4)
    except FileNotFoundError:
        raise
    except OSError as e:
        raise OSError(f"Could not read {filepath!r}: {e}") from e

    if len(header) < 4:
        # File is shorter than the magic number itself
        return False

    try:
        fourCC = header.decode("utf-8")
    except UnicodeDecodeError:
        # Not valid text -> definitely not a match, not a crash
        return False

    return fourCC == str_check


def read_scan(filepath: str) -> Scan:
    return Scan(filepath, check_fourCC(filepath, SCAN_4CC_STR))


def read_bri(filepath: str) -> Roi:
    return Roi(filepath, check_fourCC(filepath, ROI_4CC_STR))


def read_bps(filepath: str) -> Bps:
    return Bps(filepath, check_fourCC(filepath, BPS_4CC_STR))


def read_raw(filepath: str, fileheader: str, blockStart: int = 1, blockEnd: int = 1) -> Raw:
    return Raw(filepath, fileheader, blockStart, blockEnd)


def dispatch_extension(
    filepath: str, fileheader: str | None, blockStart: int = 1, blockEnd: int = 1
) -> Scan | Bps | Roi | Raw:
    if filepath.endswith(".scan"):
        return read_scan(filepath)
    elif filepath.endswith(".bps"):
        return read_bps(filepath)
    elif filepath.endswith(".bri"):
        return read_bri(filepath)
    elif filepath.endswith(".raw"):
        if not fileheader:
            raise ValueError(f"{filepath!r} is a .raw file but no fileheader was provided")
        if not fileheader.endswith(".hraw"):
            raise ValueError(f"fileheader {fileheader!r} must end with .hraw for a .raw file")
        return read_raw(filepath, fileheader, blockStart, blockEnd)
    else:
        raise ValueError(f"Unsupported file extension for {filepath!r}")


def open_path(
    path: str, path2: str | None = None, blockStart: int = 1, blockEnd: int = 1
) -> Union[Scan, Bps, Roi, Raw]:
    if not os.path.isfile(path):
        raise FileNotFoundError(
            2, "The following file does not exist", path
        )

    if path2 is not None and not os.path.isfile(path2):
        raise FileNotFoundError(
            2, "The following file does not exist", path2
        )

    return dispatch_extension(path, path2, blockStart, blockEnd)
