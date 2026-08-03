import pytest
import os
from pyiconeus import open_path
from pyiconeus.io.base import check_fourCC

def test_invalid_file_open_path():
    with pytest.raises(FileNotFoundError) as exception:
        open_path("invalidfileordirectory")
    assert (
        str(exception.value)
        == "[Errno 2] The following file does not exist: 'invalidfileordirectory'"
    )


def test_invalid_file_open_path2():
    with pytest.raises(FileNotFoundError) as exception:
        open_path("./tests/data/2DScan_v2.raw", "invalidfileordirectory")
    assert (
        str(exception.value)
        == "[Errno 2] The following file does not exist: 'invalidfileordirectory'"
    )


def test_valid_format_invalid_content():
    with pytest.raises(OSError) as exception:
        open_path("./tests/data/empty.scan")
    assert (str(exception.value) == "Unable to synchronously open file (file signature not found)")


def test_fourCC_header_length():
    with open("tmp.scan", "wb") as f:
        f.write(b'no')
        f.close()
    assert not check_fourCC("tmp.scan", "scan")
    os.remove("tmp.scan")


def test_fourCC_Non_Unicode():
    with open("tmp.scan", "wb") as f:
        f.write(b"\xff\xfe\x00\x01")
        f.close()
    assert not check_fourCC("tmp.scan", "scan")
    os.remove("tmp.scan")


def test_fourCC_unreadable_file():
    with pytest.raises(OSError) as exception:
        check_fourCC("./tests/data", "scan") # Read directory
    assert exception is not None


def test_open_raw_missing_header():
    with pytest.raises(ValueError) as exception:
        open_path( "./tests/data/2DScan_v2.raw")
    assert exception is not None
    assert str(exception.value) == "'./tests/data/2DScan_v2.raw' is a .raw file but no fileheader was provided"


def test_open_raw_invalid_header_extention():
    with pytest.raises(ValueError) as exception:
        open_path( "./tests/data/2DScan_v2.raw", "./tests/data/Mouse.bps")
    assert exception is not None
    assert str(exception.value) == "fileheader './tests/data/Mouse.bps' must end with .hraw for a .raw file"

def test_raw_wrong_block_number():
    with pytest.raises(RuntimeError) as exception:
        open_path( "./tests/data/2DScan_v2.raw", "./tests/data/2DScan_v2.hraw", 5, 3)
    assert str(exception.value) == "blockEnd must be greater or equal to blockStart"
