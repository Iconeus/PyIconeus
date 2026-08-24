# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import os

from ..models.Bps import Bps
from ..models.Raw import Raw
from ..models.Roi import Roi
from ..models.Scan import Scan

SCAN_4CC_STR = "scan"
ROI_4CC_STR = "bri_"
BPS_4CC_STR = "bps_"


def check_fourCC(filepath: str | os.PathLike[str], str_check: str) -> bool:
    """Check whether a file's leading 4-byte magic number matches str_check."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(4)
    except OSError as e:
        raise OSError(f"Could not read {filepath!r}: {e}") from e

    if len(header) < 4:
        return False

    try:
        fourCC = header.decode("utf-8")
    except UnicodeDecodeError:
        return False

    return fourCC == str_check


def read_scan(filepath: str | os.PathLike[str]) -> Scan:
    return Scan(filepath, check_fourCC(filepath, SCAN_4CC_STR))


def read_bri(filepath: str | os.PathLike[str]) -> Roi:
    return Roi(filepath, check_fourCC(filepath, ROI_4CC_STR))


def read_bps(filepath: str | os.PathLike[str]) -> Bps:
    return Bps(filepath, check_fourCC(filepath, BPS_4CC_STR))


def read_raw(
    filepath: str | os.PathLike[str],
    fileheader: str | os.PathLike[str],
    blockStart: int = 1,
    blockEnd: int = 1,
) -> Raw:
    return Raw(filepath, fileheader, blockStart, blockEnd)


def dispatch_extension(
    filepath: str | os.PathLike[str],
    fileheader: str | os.PathLike[str] | None,
    blockStart: int = 1,
    blockEnd: int = 1,
) -> Scan | Bps | Roi | Raw:
    """Returns the correct PyIconeus object by checking the file format of the given path"""
    filepath = os.fspath(filepath)
    fileheader = os.fspath(fileheader) if fileheader is not None else None
    extension = os.path.splitext(filepath)[1].lower()
    if extension == ".scan":
        return read_scan(filepath)
    elif extension == ".bps":
        return read_bps(filepath)
    elif extension == ".bri":
        return read_bri(filepath)
    elif extension == ".raw":
        if not fileheader:
            raise ValueError(
                f"{filepath!r} is a .raw file but no fileheader was provided"
            )
        if os.path.splitext(fileheader)[1].lower() != ".hraw":
            raise ValueError(
                f"fileheader {fileheader!r} must end with .hraw for a .raw file"
            )
        return read_raw(filepath, fileheader, blockStart, blockEnd)
    else:
        raise ValueError(f"Unsupported file extension for {filepath!r}")


def open_path(
    path: str | os.PathLike[str],
    path2: str | os.PathLike[str] | None = None,
    blockStart: int = 1,
    blockEnd: int = 1,
) -> Scan | Bps | Roi | Raw:
    """Main IO function.
    Checks if the file exist, then dispatch the path in the correct function.

    Last three parameters are optional for all files types except '.raw' files which needs to be paired with their corresponding '.hraw' file in the path2 parameter

    Parameters
    ----------

    **path**: str
        File path of the wanted PyIconeus object
    **path2**: str (optional)
        File path of the header file. (Only used with .raw files)
    **blockStart**: int = 1 (optional)
        The starting block number to get from the raw data
    **blockEnd**: int = 1 (optional)
        The last block for the raw data

    Returns
    -------

    PyIconeus object depending of the given file
    """
    path = os.fspath(path)
    path2 = os.fspath(path2) if path2 is not None else None
    if not os.path.isfile(path):
        raise FileNotFoundError(2, "The following file does not exist", path)

    if (
        os.path.splitext(path)[1].lower() == ".raw"
        and path2 is not None
        and not os.path.isfile(path2)
    ):
        raise FileNotFoundError(2, "The following file does not exist", path2)

    return dispatch_extension(path, path2, blockStart, blockEnd)
