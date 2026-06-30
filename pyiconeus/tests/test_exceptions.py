from src.io.base import read_scan
from src.io.base import open_path
from src.models.Scan import Scan

# from src.models.exceptions import BadFile
from src.io.base import check_fourCC
import pytest


def test_bad_file_check_fourCC():
    with pytest.raises(FileNotFoundError) as exception:
        check_fourCC("NotAFile!")
    assert str(exception.value) == "[Errno 2] No such file or directory: 'NotAFile!'"


def test_invalid_file_open_path():
    with pytest.raises(FileNotFoundError) as exception:
        open_path("invalidfileordirectory")
    assert (
        str(exception.value)
        == "[Errno 2] The following file does not exist: 'invalidfileordirectory'"
    )


def test_valid_format_invalid_content():
    # Needs to be changed, interprets it as a scan v1 and return None
    open_path(".\\tests\\data\\empty.scan") is None
