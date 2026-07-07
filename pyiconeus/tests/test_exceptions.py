# from src.models.exceptions import BadFile
import pytest

from pyiconeus.io.base import SCAN_4CC_STR, check_fourCC, open_path


def test_invalid_file_open_path():
    with pytest.raises(FileNotFoundError) as exception:
        open_path("invalidfileordirectory")
    assert (
        str(exception.value)
        == "[Errno 2] The following file does not exist: 'invalidfileordirectory'"
    )


def test_valid_format_invalid_content():
    # Needs to be changed, interprets it as a scan v1 and return None
    with pytest.raises(OSError) as exception:
        open_path(".\\tests\\data\\empty.scan") is None
    assert (str(exception.value) == "Unable to synchronously open file (file signature not found)")
