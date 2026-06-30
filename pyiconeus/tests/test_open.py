from pyiconeus.io.base import open_path

testDataPath = "./tests/data"


def test_open():
    scan = open_path(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan"
    )
    assert scan is not None
    scan = open_path(testDataPath + "/TestULM2D_v2.source.scan")
    assert scan is not None


def test_open_bps():
    bps = open(testDataPath + "/Mouse.bps")
    assert bps is not None
