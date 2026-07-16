import numpy as np
from pyiconeus.io.base import SCAN_4CC_STR, check_fourCC
from pyiconeus.models.Scan import Scan, AcquisitionMode, WeightUnitType


def test_check_fourCC():
    assert check_fourCC(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan",
        SCAN_4CC_STR,
    )


def test_scan():
    scan = Scan(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan", True
    )
    assert scan is not None
    assert scan.acquisitionMode == AcquisitionMode._4DScan


def test_scan_ULM_2D():
    scan = Scan("./tests/data" + "/TestULM2D_v2.source.scan", True)
    print(scan)
    assert scan is not None
    assert scan.acquisitionMode == AcquisitionMode._2DScan
    assert scan.sizeY == 1


def test_scan_values():
    scan = Scan(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan", True
    )
    assert scan.sizeX == 103
    assert len(scan.measuredTimes) == 5200
    assert scan.type.name == "Source"


def test_scan_values_ULM_2D():
    scan: Scan = Scan("./tests/data" + "/TestULM2D_v2.source.scan", True)
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
    scan: Scan = Scan("./tests/data" + "/TestULM2D_v2.source.scan", True)
    vTp = scan.get_VoxelToProbe()
    print("VoxelToProbeCreation")
    print(vTp)
    assert vTp is not None
    assert vTp.shape == np.ndarray((4,4)).shape


def test_load_v1():
    scanv1: Scan = Scan(
        "./tests/data" + "/4Dscan_1_StimVIS16__60_30_60_8_fus3D.source.scan", False
    )
    assert scanv1 is not None
    assert scanv1.nPose == 1 # consolidated


def test_compare_v1_v2_scanmetaData():
    scanv1: Scan = Scan(
        "./tests/data" + "/4Dscan_1_StimVIS16__60_30_60_8_fus3D.source.scan", False
    )
    scanv2: Scan = Scan(
        "./tests/data" + "/4Dscan_1_StimVIS16__60_30_60_8_fus3Dv2.source.scan", True
    )
    assert scanv1.projectTag == scanv2.projectTag
    assert scanv1.projectDescription == scanv2.projectDescription
    assert scanv1.ageAtTransfer == scanv2.ageAtTransfer
    assert scanv1.subjectTag == scanv2.subjectTag
    assert scanv1.sessionTag == scanv2.sessionTag
    assert scanv1.species == scanv2.species
    assert scanv1.gender == scanv2.gender
    assert scanv1.transferDate == scanv2.transferDate
    assert scanv1.ageAtTransfer == scanv2.ageAtTransfer
    assert scanv1.subjectDescription == scanv2.subjectDescription
    assert scanv1.weightUnit == scanv2.weightUnit
    assert scanv1.weight == scanv2.weight
    assert scanv1.treatment == scanv2.treatment
    assert scanv1.scanTag == scanv2.scanTag
    assert scanv1.studyType == scanv2.studyType
    assert scanv1.taskName == scanv2.taskName
    assert scanv1.taskDescription == scanv2.taskDescription
    assert scanv1.username == scanv2.username
    assert scanv1.acquisitionDate == scanv2.acquisitionDate
    assert scanv1.type == scanv2.type
    assert scanv1.icoScanVersion is not None
    assert scanv2.icoScanVersion is not None
    assert scanv1.icoScanVersion.major == scanv2.icoScanVersion.major
    assert scanv1.icoScanVersion.minor == scanv2.icoScanVersion.minor
    assert scanv1.icoScanVersion.patch == scanv2.icoScanVersion.patch


def test_compare_acqMetaData():
    scanv1: Scan = Scan(
        "./tests/data/4Dscan_1_StimVIS16__60_30_60_8_fus3D.source.scan", False
    )
    scanv2: Scan = Scan(
        "./tests/data/4Dscan_1_StimVIS16__60_30_60_8_fus3Dv2.source.scan", True
    )
    assert scanv1.sizeX == scanv2.sizeX
    assert scanv1.sizeY * scanv1.nPose == scanv2.sizeY
    assert scanv2.nPose == 1
    assert scanv1.nTime == scanv2.nTime
    assert len(scanv1.measuredTimes) == len(scanv2.measuredTimes)
    assert len(scanv1.theoricalTimeIndices) == len(scanv2.theoricalTimeIndices)
    assert scanv1.voxDim.dx == scanv2.voxDim.dx
    assert round(scanv1.voxDim.dy, 6) == round(scanv2.voxDim.dy, 6)
    assert scanv1.voxDim.dz == scanv2.voxDim.dz
    assert scanv1.voxDim.dt == scanv2.voxDim.dt
    assert scanv1.voxDim.dtheta == scanv2.voxDim.dtheta
    assert scanv1.acquisitionMode == scanv2.acquisitionMode
    assert scanv1.ultrafastSamplingFrequency == scanv2.ultrafastSamplingFrequency
    assert scanv1.pulseRepetitionFrequency == scanv2.pulseRepetitionFrequency
    assert scanv1.ultrafastTransmitFrequency == scanv2.ultrafastTransmitFrequency
    assert scanv1.transmitVoltage == scanv2.transmitVoltage
    assert len(scanv1.planeWaveAngles) == len(scanv2.planeWaveAngles)
    assert scanv1.delayAfterTrigger == scanv2.delayAfterTrigger
    assert scanv1.integrationWindowDuration == scanv2.integrationWindowDuration
    assert scanv1.voxels.shape == np.ndarray(shape=(105, 16, 87, 325, 1, 1)).shape


def test_scan_tomo():
    scan: Scan = Scan("./tests/data" + "/Tomographie_Compound.scan", False)
    assert scan is not None
    assert scan.ultrafastSamplingFrequency == 62.5
