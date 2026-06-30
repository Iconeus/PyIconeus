from tests.test_open import testDataPath
from pyiconeus.models.Scan import Scan
from pyiconeus.models.Bps import Bps
from pyiconeus.io.base import open_path


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

if __name__ == '__main__':
    test_assign_bps()