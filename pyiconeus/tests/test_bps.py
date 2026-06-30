from src.io.base import open_path
from tests.test_open import testDataPath
from src.models.Bps import Bps
from src.models.Scan import Scan


def test_bps_load():
    bps = open_path(testDataPath + "/Mouse.bps")
    assert bps is not None


def test_print_bps():
    bps = open_path(testDataPath + "/Mouse.bps")
    # Add --capture=no stdout to see BPS
    print(bps.data)  # ty:ignore[unresolved-attribute]
    assert bps is not None


def test_assign_bps():
    scan: Scan = open_path(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan"
    )  # ty:ignore[invalid-assignment]
    bps: Bps = open_path(testDataPath + "/Mouse.bps")  # ty:ignore[invalid-assignment]
    scan.bps = bps
    assert scan.bps is not None
