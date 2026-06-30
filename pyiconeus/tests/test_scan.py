from tests.test_open import testDataPath
from src.io.base import read_scan
from src.models.Scan import Scan
from src.io.base import check_fourCC
from src.models.Scan import AcquisitionMode, WeightUnitType


def test_check_fourCC():
    assert check_fourCC(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan"
    )


def test_scan():
    scan = read_scan(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan"
    )
    assert scan is not None


def test_scan_ULM_2D():
    scan = read_scan(testDataPath + "/TestULM2D_v2.source.scan")
    assert scan is not None


def test_scan_values():
    scan = read_scan(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan"
    )
    assert scan.sizeX == 103  # ty:ignore[unresolved-attribute]
    assert len(scan.measuredTimes) == 5200  # ty:ignore[unresolved-attribute]
    assert scan.type.name == "Source"  # ty:ignore[unresolved-attribute]


def test_scan_values_ULM_2D():
    scan: Scan = read_scan(testDataPath + "/TestULM2D_v2.source.scan")  # ty:ignore[invalid-assignment]
    assert scan.sizeX == 128
    assert scan.sizeY == 1
    assert scan.sizeZ == 91
    assert scan.nPose == 1
    assert scan.nTime == 9
    assert scan.dim6.dim6 == 1
    assert len(scan.measuredTimes) == 9
    assert len(scan.theoricalTimeIndices) == 9
    assert scan.acquisitionMode == AcquisitionMode._2DScan
    assert scan.probe.name == "IcoPrime"
    assert scan.weight == 0.0
    assert scan.weightUnit == WeightUnitType.mg
    assert scan.type.name == "Source"
