import sys
import ctypes
import struct
import numpy as np
from ...models.Scan import Scan, Dim6, VoxDim, Probe, ProbeToLabElements, AcquisitionMode, Depth, GenderType, IcoScanVersion, WeightUnitType, ScanType
from ...utils.utils import read_string_binary
import datetime
import pytz


def read_dim6(scan: Scan, f) -> None:
    scan.dim6  = Dim6(struct.unpack('@Q', f.read(8))[0])
    dim6intents = []
    for _ in range((int)(scan.dim6.dim6)):
        dim6intents.append(struct.unpack('@L', f.read(4))[0])
    for dim6intent in dim6intents:
        if dim6intent == 1 or dim6intent == 3:
            f.seek(20)
        elif dim6intent == 0:
            clutterFilterType = struct.unpack('@L', f.read(4))[0]
            clutterFilterWindowDuration = struct.unpack('@d', f.read(8))[0]
            if clutterFilterType == 0 or clutterFilterType == 1:
                clutterFilterCutoffLow = struct.unpack('@L', f.read(4))[0]
                clutterFilterCutoffHigh = struct.unpack('@L', f.read(4))[0]
            elif clutterFilterType == 2:
                clutterFilterCutoffLow = struct.unpack('@f', f.read(4))[0]
                clutterFilterCutoffHigh = struct.unpack('@f', f.read(4))[0]
            scan.dim6.dim6element.add((Dim6.Dim6type(dim6intent), Dim6.ClutterFiltering(clutterFilterType, clutterFilterWindowDuration,
                                                                         clutterFilterCutoffLow, clutterFilterCutoffHigh)))
        elif dim6intent == 2:
            velocityMin = struct.unpack('@f', f.read(4))[0]
            velocityMax = struct.unpack('@f', f.read(4))[0]
            f.seek(12)
            scan.dim6.dim6element.add((Dim6.Dim6type(dim6intent), Dim6.VelocityBandwidthFiltering(velocityMin, velocityMax)))


def read_voxDim(scan: Scan, f) -> None:
    dx = struct.unpack('@d', f.read(8))[0]
    dy = struct.unpack('@d', f.read(8))[0]
    dz = struct.unpack('@d', f.read(8))[0]
    dt = struct.unpack('@d', f.read(8))[0]
    dr = struct.unpack('@d', f.read(8))[0]
    dtheta = struct.unpack('@d', f.read(8))[0]
    scan.voxDim = VoxDim(dx, dy, dz, dt, dr, dtheta)

def read_data(scan: Scan, f) -> None:
    dataSize = scan.sizeX * scan.sizeY * scan.sizeZ * scan.nTime * scan.nPose * scan.dim6.dim6
    dataArray: np.ndarray = np.ndarray(dataSize)
    for i in range(dataSize):
        dataArray[i] = struct.unpack('@d', f.read(8))[0]
    scan.voxels = np.reshape(dataArray, shape=(scan.sizeX, scan.sizeY, scan.sizeZ, scan.nTime, scan.nPose, scan.dim6.dim6))


def read_porbe_transform(scan: Scan, f) -> ProbeToLabElements:
    probeElement = ProbeToLabElements(scan.nPose)
    for _ in range(scan.nPose):
        x = struct.unpack('@d', f.read(8))[0]
        y = struct.unpack('@d', f.read(8))[0]
        z = struct.unpack('@d', f.read(8))[0]
        probeElement.matricesList.append(ProbeToLabElements.ProbeToLabMatrices(x, y, z))
    return probeElement

def read_probeInfo(scan: Scan, f) -> None:
    probeType = struct.unpack('@L', f.read(4))[0]
    probeCentralFrequency = struct.unpack('@d', f.read(8))[0]
    probePitch = struct.unpack('@d', f.read(8))[0]
    probeElevationAperture = struct.unpack('@d', f.read(8))[0]
    f.seek(8, 1)
    probeRadiusOfCurvature = struct.unpack('@d', f.read(8))[0]
    probeNumberOfElements = struct.unpack('@H', f.read(2))[0]
    probeModel = read_string_binary(f, '@H', 2)
    probeName = read_string_binary(f, '@H', 2)
    scan.probe = Probe(probeName,
                            Probe.ProbeType(probeType),
                            probeCentralFrequency,
                            probePitch,
                            probeElevationAperture,
                            probeRadiusOfCurvature,
                            probeNumberOfElements,
                            probeModel)


def read_binary(filepath) -> Scan:
    scan: Scan = Scan()
    with open(filepath, 'rb') as f:
        f.seek(32)
        dO: int = struct.unpack('@Q', f.read(8))[0]
        f.seek(92)
        scan.sizeX = struct.unpack('@Q', f.read(8))[0]
        scan.sizeY = struct.unpack('@Q', f.read(8))[0]
        scan.sizeZ = struct.unpack('@Q', f.read(8))[0]
        scan.nTime = struct.unpack('@Q', f.read(8))[0]
        scan.nPose = struct.unpack('@Q', f.read(8))[0]
        read_dim6(scan, f)
        read_voxDim(scan, f)
        timeArraySize: int = scan.sizeY * scan.nTime * scan.nPose
        for _ in range(timeArraySize):
            scan.measuredTimes.append(struct.unpack('@d', f.read(8))[0])
        for _ in range(timeArraySize):
            scan.theoricalTimeIndices.append(struct.unpack('@L', f.read(4))[0])
        scan.probeToLabsTranslations = read_porbe_transform(scan, f)
        scan.probeToLabsRotations = read_porbe_transform(scan, f)
        f.seek(4, 1)
        scan.acquisitionMode = AcquisitionMode(struct.unpack('@L', f.read(4))[0])
        f.seek(4, 1)
        read_probeInfo(scan, f)
        depthNear = struct.unpack('@d', f.read(8))[0]
        depthFar = struct.unpack('@d', f.read(8))[0]
        scan.depth = Depth(depthNear, depthFar)
        scan.ultrafastTransmitFrequency = struct.unpack('@d', f.read(8))[0]
        scan.pulseRepetitionFrequency = struct.unpack('@d', f.read(8))[0]
        scan.ultrafastSamplingFrequency = struct.unpack('@d', f.read(8))[0]
        f.seek(8, 1)
        nPlaneWavesAngles = struct.unpack('@L', f.read(4))[0]
        for _ in range(nPlaneWavesAngles):
            scan.planeWaveAngles.append(struct.unpack('@d', f.read(8))[0])
        tempVal = struct.unpack('@L', f.read(4))
        f.seek(tempVal[0] * 24 + 8, 1)
        scan.transmitVoltage = struct.unpack('@d', f.read(8))[0]
        f.seek(4, 1)
        scan.delayAfterTrigger = struct.unpack('@d', f.read(8))[0]
        tempVal = struct.unpack('@L', f.read(4))
        f.seek(tempVal[0] * 8, 1)
        scan.isMultiplane = struct.unpack('@?', f.read(1))[0]
        f.seek(1, 1)
        scan.integrationWindowDuration = struct.unpack('@d', f.read(8))[0]
        scan.sequenceName = read_string_binary(f, '@L', 4)
        scan.projectTag = read_string_binary(f, '@L', 4)
        scan.projectDescription = read_string_binary(f, '@L', 4)
        scan.subjectTag = read_string_binary(f, '@L', 4)
        scan.sessionTag = read_string_binary(f, '@L', 4)
        scan.species = read_string_binary(f, '@L', 4)
        scan.gender = GenderType(struct.unpack('@L', f.read(4))[0])
        scan.transferDate = datetime.datetime.fromtimestamp(struct.unpack('@q', f.read(8))[0], pytz.utc)
        scan.ageAtTransfer = struct.unpack('@Q', f.read(8))[0]
        scan.subjectDescription = read_string_binary(f, '@L', 4)
        scan.weightUnit = WeightUnitType(struct.unpack('@L', f.read(4))[0])
        scan.weight = struct.unpack('@f', f.read(4))[0]
        scan.treatment = read_string_binary(f, '@L', 4)
        scan.scanTag = read_string_binary(f, '@L', 4)
        scan.studyType = read_string_binary(f, '@L', 4)
        scan.taskName = read_string_binary(f, '@L', 4)
        scan.taskDescription = read_string_binary(f, '@L', 4)
        scan.username = read_string_binary(f, '@L', 4)
        for _ in range(2):
            tempVal = struct.unpack('@L', f.read(4))[0]
            f.seek(tempVal, 1)
        scan.acquisitionDate = datetime.datetime.fromtimestamp(struct.unpack('@q', f.read(8))[0], pytz.utc)
        scan.type = ScanType(struct.unpack('@L', f.read(4))[0])
        scan.stimulationToggleTimes = read_string_binary(f, '@L', 4)
        icoScanMajor = struct.unpack('@L', f.read(4))[0]
        icoScanMinor = struct.unpack('@L', f.read(4))[0]
        icoScanPatch = struct.unpack('@L', f.read(4))[0]
        scan.icoScanVersion = IcoScanVersion(icoScanMajor, icoScanMinor, icoScanPatch)
        f.seek(dO)
        read_data(scan, f)
    f.close()
    return scan

if __name__ == '__main__':
    if (len(sys.argv)) != 2:
        raise Exception("Invalid number of arguments")
    print(read_binary(sys.argv))
