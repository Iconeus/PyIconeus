from pyiconeus.io.base import open_path

testDataPath = "./tests/data"


# Scan open
def test_open_scan_v2():
    scan = open_path(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan"
    )
    assert scan is not None
    scan = open_path(testDataPath + "/TestULM2D_v2.source.scan")
    assert scan is not None


# Bps open
def test_open_bps():
    bps = open_path(testDataPath + "/Mouse.bps")
    assert bps is not None


def test_open_bps_v2():
    bps = open_path(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.bps"
    )
    assert bps is not None


# Roi open
def test_open_roi():
    roi = open_path(testDataPath + "/roi_for_4DStacked.bri")
    assert roi is not None


def test_open_roi_binary():
    roi = open_path(testDataPath + "/roiread_binary.bri")
    assert roi is not None


# Raw read
def test_open_raw_missing_header():
    raw = open_path(testDataPath + "/TestULM2D_v2.raw")
    assert raw is None


def test_open_raw():
    raw = open_path(
        testDataPath + "/TestULM2D_v2.raw", testDataPath + "/TestULM2D_v2.hraw"
    )
    assert raw is not None
