import numpy as np
from pytest import mark
from pyiconeus.io.base import SCAN_4CC_STR, check_fourCC
from pyiconeus.models.Scan import Scan, AcquisitionMode, WeightUnitType, Probe


def test_check_fourCC():
    assert check_fourCC(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan",
        SCAN_4CC_STR,
    )


def test_scan():
    scan = Scan(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan", True
    )
    assert isinstance(scan, Scan)
    assert scan.acquisitionMode == AcquisitionMode._4DScan


@mark.filterwarnings("ignore::RuntimeWarning")
def test_2D_Scan():
    scan = Scan("./tests/data" + "/2DScan_v2.source.scan", True)
    print(scan)
    assert isinstance(scan, Scan)
    assert scan.acquisitionMode == AcquisitionMode._2DScan
    assert scan.sizeY == 1
    scan = Scan("./tests/data" + "/2DScan.source.scan", False)
    print(scan)
    assert isinstance(scan, Scan)
    assert scan.acquisitionMode == AcquisitionMode._2DScan
    assert scan.sizeY == 1


def test_3D_Scan():
    scan = Scan(
        "./tests/data/"
        + "sub-souris1_ses-Session_2021-3-9_Angio3Dscan_angio3D.source.scan",
        False,
    )
    assert isinstance(scan, Scan)
    assert scan.acquisitionMode == AcquisitionMode._3DScan


def test_scan_values():
    scan = Scan(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan", True
    )
    assert scan.sizeX == 103
    assert len(scan.measuredTimes) == 5200
    assert scan.type.name == "Source"


def test_scan_values_ULM_2D():
    scan: Scan = Scan("./tests/data" + "/2DScan_v2.source.scan", True)
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
    scan: Scan = Scan("./tests/data" + "/2DScan_v2.source.scan", True)
    vTp = scan.get_VoxelToProbe()
    print("VoxelToProbeCreation")
    print(vTp)
    assert vTp is not None
    assert vTp.shape == np.ndarray((4, 4)).shape


def test_load_v1():
    scanv1: Scan = Scan(
        "./tests/data" + "/4Dscan_1_StimVIS16__60_30_60_8_fus3D.source.scan", False
    )
    assert isinstance(scanv1, Scan)
    assert scanv1.nPose == 1


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


def test_compare_matrices():
    scanv1: Scan = Scan(
        "./tests/data/4Dscan_1_StimVIS16__60_30_60_8_fus3D.source.scan", False
    )
    scanv2: Scan = Scan(
        "./tests/data/4Dscan_1_StimVIS16__60_30_60_8_fus3Dv2.source.scan", True
    )

    assert isinstance(scanv1, Scan)
    assert isinstance(scanv2, Scan)
    ptl1 = scanv1.get_ProbeToLab()[0]
    ptl2 = scanv2.get_ProbeToLab()[0]
    assert np.allclose(ptl1, ptl2)


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


def test_4DCustomScan():
    scan: Scan = Scan("./tests/data" + "/020222_M297_SHAM_4DfUS1.scan", False)
    scanv2: Scan = Scan("./tests/data" + "/020222_M297_SHAM_4DfUS1.v2.scan", True)
    assert isinstance(scan, Scan)
    assert scan.probeToLabsTranslations.shape[0] == 3
    assert scan.sizeX == 128
    assert scan.nTime == 572
    assert scan.nPose == 3
    assert scanv2.nPose == scan.nPose
    assert scan.sizeX == scanv2.sizeX
    assert scan.sizeY == scanv2.sizeY
    assert scanv2.nPose == 3
    assert scan.nTime == scanv2.nTime
    assert len(scan.measuredTimes) == len(scanv2.measuredTimes)
    assert len(scan.theoricalTimeIndices) == len(scanv2.theoricalTimeIndices)
    assert scan.voxDim.dx == scanv2.voxDim.dx
    assert round(scan.voxDim.dy, 6) == round(scanv2.voxDim.dy, 6)
    assert scan.voxDim.dz == scanv2.voxDim.dz
    assert scan.voxDim.dt == scanv2.voxDim.dt
    assert scan.voxDim.dtheta == scanv2.voxDim.dtheta
    assert scan.acquisitionMode == scanv2.acquisitionMode
    assert scan.ultrafastSamplingFrequency == scanv2.ultrafastSamplingFrequency
    assert scan.pulseRepetitionFrequency == scanv2.pulseRepetitionFrequency
    assert scan.ultrafastTransmitFrequency == scanv2.ultrafastTransmitFrequency
    assert scan.transmitVoltage == scanv2.transmitVoltage
    assert len(scan.planeWaveAngles) == len(scanv2.planeWaveAngles)
    assert scan.delayAfterTrigger == scanv2.delayAfterTrigger
    assert scan.integrationWindowDuration == scanv2.integrationWindowDuration
    assert scan.voxels.shape == scanv2.voxels.shape


def test_RCA_loading():
    scan: Scan = Scan(
        "./tests/data" + "/4Dscan_1_15_15_15_8_fus3D.source_v2.scan", True
    )
    assert isinstance(scan, Scan)
    assert scan.probe.probeType == Probe.ProbeType.RCA
    assert scan.probe.name == "IcoPrime"
    scan = Scan("./tests/data/" + "RCA_4Dscan_2_fus3D.source.scan", False)
    assert isinstance(scan, Scan)
    assert scan.probe.probeType == Probe.ProbeType.RCA
    assert scan.acquisitionMode == AcquisitionMode._4DscanRCA


if __name__ == "__main__":
    test_compare_matrices()
