# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import os

import pytest

from pyiconeus import open_path
from pyiconeus.utils.utils import check_fourCC


def test_invalid_file_open_path():
    with pytest.raises(FileNotFoundError) as exception:
        open_path("invalidfileordirectory")
    assert (
        str(exception.value)
        == "[Errno 2] The following file does not exist: 'invalidfileordirectory'"
    )


def test_invalid_file_open_path2(data_path):
    with pytest.raises(FileNotFoundError) as exception:
        open_path(data_path("2DScan_v2.raw"), "invalidfileordirectory")
    assert (
        str(exception.value)
        == "[Errno 2] The following file does not exist: 'invalidfileordirectory'"
    )


def test_valid_format_invalid_content(data_path):
    with pytest.raises(OSError) as exception:
        open_path(data_path("empty.scan"))
    assert (
        str(exception.value)
        == "Unable to synchronously open file (file signature not found)"
    )


def test_fourCC_header_length():
    with open("tmp.scan", "wb") as f:
        f.write(b"no")
        f.close()
    assert not check_fourCC("tmp.scan", "scan")
    os.remove("tmp.scan")


def test_fourCC_Non_Unicode():
    with open("tmp.scan", "wb") as f:
        f.write(b"\xff\xfe\x00\x01")
        f.close()
    assert not check_fourCC("tmp.scan", "scan")
    os.remove("tmp.scan")


def test_fourCC_unreadable_file(data_path):
    directory = os.path.dirname(data_path("Mouse.bps"))
    with pytest.raises(OSError) as exception:
        check_fourCC(directory, "scan")
    assert exception is not None


def test_open_raw_missing_header(data_path):
    raw = data_path("2DScan_v2.raw")
    with pytest.raises(ValueError) as exception:
        open_path(raw)
    assert exception is not None
    assert (
        str(exception.value)
        == f"'{raw}' is a .raw file but no fileheader was provided"
    )


def test_open_raw_invalid_header_extention(data_path):
    header = data_path("Mouse.bps")
    with pytest.raises(ValueError) as exception:
        open_path(data_path("2DScan_v2.raw"), header)
    assert exception is not None
    assert (
        str(exception.value)
        == f"fileheader '{header}' must end with .hraw for a .raw file"
    )


def test_raw_wrong_block_number(data_path):
    with pytest.raises(RuntimeError) as exception:
        open_path(data_path("2DScan_v2.raw"), data_path("2DScan_v2.hraw"), 5, 3)
    assert str(exception.value) == "blockEnd must be greater or equal to blockStart"


def test_3D_Scan(data_path):
    with pytest.raises(RuntimeError) as exception:
        open_path(
            data_path(
                "sub-Mouse001_ses-Session_2021-6-24_3Dscan_2_tomo_angio3D.source.scan"
            )
        )
    assert (
        str(exception.value)
        == "Could not decompose probe tforms into center, translations and rotations."
    )


def test_invalid_file_format(data_path):
    txt = data_path("notAScan.txt")
    with pytest.raises(ValueError) as exception:
        open_path(txt)
    assert str(exception.value) == f"Unsupported file extension for '{txt}'"


def test_irrelevant_header_is_not_validated(data_path):
    scan = open_path(data_path("2DScan_v2.source.scan"), "missing.hraw")
    assert scan is not None
