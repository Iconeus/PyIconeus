import pyiconeus
import os
from pytest import mark

# Scan open
def test_open_scan_v2():
    scan = pyiconeus.open_path(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan"
    )
    assert scan is not None
    scan = pyiconeus.open_path("./tests/data" + "/TestULM2D_v2.source.scan")
    assert scan is not None


# Bps open
def test_open_bps():
    bps = pyiconeus.open_path("./tests/data" + "/Mouse.bps")
    assert bps is not None


def test_open_bps_v2():
    bps = pyiconeus.open_path(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.bps"
    )
    assert bps is not None


# Roi open
def test_open_roi():
    roi = pyiconeus.open_path("./tests/data" + "/roi_for_4DStacked.bri")
    assert roi is not None


def test_open_roi_binary():
    roi = pyiconeus.open_path("./tests/data" + "/roiread_binary.bri")
    assert roi is not None


def test_open_raw():
    raw = pyiconeus.open_path(
        "./tests/data" + "/TestULM2D_v2.raw", "./tests/data" + "/TestULM2D_v2.hraw"
    )
    assert raw is not None

@mark.filterwarnings("ignore::RuntimeWarning")
def test_open_all():
    directory = os.fsencode("./tests/data")

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename == "020222_M297_SHAM_4DfUS1.scan":
            icoFile = pyiconeus.open_path("./tests/data" + "/" + filename)
        elif filename == "empty.scan":
            continue
        elif filename.endswith(".hraw"):
            icoFile = pyiconeus.open_path("./tests/data" + "/" + filename.split('.')[0] + ".raw", "./tests/data" + "/" + filename)
        elif filename.endswith(".raw"):
            icoFile = pyiconeus.open_path("./tests/data" + "/" + filename, "./tests/data" + "/" + filename.split('.')[0] + ".hraw")
        else:
            icoFile = pyiconeus.open_path("./tests/data" + "/" + filename)
        print(filename)
        assert icoFile is not None
