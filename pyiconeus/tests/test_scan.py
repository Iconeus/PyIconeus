from pyiconeus.io.base import SCAN_4CC_STR, check_fourCC
from pyiconeus.models.Scan import Scan, AcquisitionMode, WeightUnitType
from tests.test_open import testDataPath


def test_check_fourCC():
    assert check_fourCC(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan",
        SCAN_4CC_STR,
    )


def test_scan():
    scan = Scan(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan", True
    )
    assert scan is not None


def test_scan_ULM_2D():
    scan = Scan(testDataPath + "/TestULM2D_v2.source.scan", True)
    print(scan)
    assert scan is not None


def test_scan_values():
    scan = Scan(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan", True
    )
    assert scan.sizeX == 103
    assert len(scan.measuredTimes) == 5200  # ty:ignore[unresolved-attribute]
    assert scan.type.name == "Source"  # ty:ignore[unresolved-attribute]


def test_scan_values_ULM_2D():
    scan: Scan = Scan(testDataPath + "/TestULM2D_v2.source.scan", True)  # ty:ignore[invalid-assignment]
    assert scan.sizeX == 128
    assert scan.sizeY == 1
    assert scan.sizeZ == 91
    assert scan.nPose == 1
    assert scan.nTime == 9
    assert scan.dim6.count == 1
    assert len(scan.measuredTimes) == 9
    assert len(scan.theoricalTimeIndices) == 9
    assert scan.acquisitionMode == AcquisitionMode._2DScan
    assert scan.probe.name == "IcoPrime"
    assert scan.weight == 0.0
    assert scan.weightUnit == WeightUnitType.mg
    assert scan.type.name == "Source"
    print(scan.voxels)


def test_voxel_to_prob():
    scan: Scan = Scan(testDataPath + "/TestULM2D_v2.source.scan", True)  # ty:ignore[invalid-assignment]
    vTp = scan.get_VoxelToProbe()
    print("VoxelToProbeCreation")
    print(vTp)
    assert vTp is not None


def test_load_v1():
    #     # scan: Scan = Scan(testDataPath + "/TestULM2D.source.scan", False)
    scanv1: Scan = Scan(
        testDataPath + "/4Dscan_1_StimVIS16__60_30_60_8_fus3D.source.scan", False
    )
    assert scanv1 is not None


def test_compare_v1_v2_metaData():
    scanv1: Scan = Scan(
        testDataPath + "/4Dscan_1_StimVIS16__60_30_60_8_fus3D.source.scan", False
    )
    scanv2: Scan = Scan(
        testDataPath + "/4Dscan_1_StimVIS16__60_30_60_8_fus3Dv2.source.scan", True
    )
    assert scanv1.projectTag == scanv2.projectTag
    assert scanv1.sessionTag == scanv2.sessionTag
    assert scanv1.subjectTag == scanv2.subjectTag
    assert scanv1.scanTag == scanv2.scanTag
    assert scanv1.acquisitionDate == scanv2.acquisitionDate


def test_scan_tomo():
    scan: Scan = Scan(testDataPath + "/Tomographie_Compound.scan", False)
    assert scan is not None


if __name__ == "__main__":
    test_scan_tomo()
