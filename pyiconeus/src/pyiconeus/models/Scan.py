import ctypes
from enum import IntEnum
import datetime
import numpy as np

from src.models.Bps import Bps

class Scan:
    def __init__(self) -> None:
        self.sizeX: int
        self.sizeY: int
        self.sizeZ: int
        self.nTime: int
        self.nPose: int
        self.measuredTimes: list[float] = []
        self.theoricalTimeIndices: list[int] = []
        self.probeToLabsTranslations: np.ndarray
        self.probeToLabsRotations: np.ndarray
        self.dim6: Dim6
        self.voxDim: VoxDim
        self.acquisitionMode: AcquisitionMode
        self.probe: Probe
        self.depth: Depth
        self.ultrafastTransmitFrequency: float
        self.pulseRepetitionFrequency: float
        self.ultrafastSamplingFrequency: float
        self.planeWaveAngles: list[float] = []
        self.transmitVoltage: float
        self.delayAfterTrigger: float
        self.isMultiplane: bool
        self.integrationWindowDuration: float
        self.sequenceName: str
        self.projectTag: str
        self.projectDescription: str
        self.subjectTag: str
        self.sessionTag: str
        self.species: str
        self.gender: GenderType
        self.transferDate: datetime.datetime
        self.ageAtTransfer: int
        self.subjectDescription: str
        self.weightUnit: WeightUnitType
        self.weight: float
        self.treatment: str
        self.scanTag: str
        self.studyType: str
        self.taskName: str
        self.taskDescription: str
        self.username: str
        self.acquisitionDate: datetime.datetime
        self.type: ScanType
        self.stimulationToggleTimes: list[float] = []
        self.icoScanVersion: IcoScanVersion
        self.voxels: np.ndarray
        self.bps: Bps

    def __repr__(self):
        ...
    def __str__(self) -> str:
        rep =  f"sizeX: {self.sizeX}\nsizeY: {self.sizeY}\nsizeZ: {self.sizeZ}\nnTime: {self.nTime}\nnPose: {self.nPose}"\
        f"\ndim6: {self.dim6}\nvoxDim: {self.voxDim}\nmeasuredTimes: {len(self.measuredTimes)} ({self.sizeY} * {self.nTime} * {self.nPose}) (sizeY * nTime * nPose)\n"\
        f"theoricalTimeIndices: {len(self.theoricalTimeIndices)} ({self.sizeY} * {self.nTime} * {self.nPose}) (sizeY * nTime * nPose)\n"\
        f"probeToLabsTranslation: {self.probeToLabsTranslations}\nprobeToLabsRotations: {self.probeToLabsRotations}\n"\
        f"acquisitionMode: {self.acquisitionMode.name[1:]}\nprobe: {self.probe}\ndepth: {self.depth}\n"\
        f"ultrafastTransmitFrequency: {self.ultrafastTransmitFrequency}\npulseRepetitionFrequency: {self.pulseRepetitionFrequency}\n"\
        f"ultrafastSamplingFrequency: {self.ultrafastSamplingFrequency}\nplaneWavesAngles: {len(self.planeWaveAngles)}\n"
        for i in range(len(self.planeWaveAngles)):
            rep += f"\t{i}: {self.planeWaveAngles[i]}\n"
        rep += f"transmitVoltage: {self.transmitVoltage}\ndelayAfterTrigger: {self.delayAfterTrigger}\nisMultiplane: {self.isMultiplane}\n"\
        f"integrationWindowDuration: {self.integrationWindowDuration}\nsequenceName: {self.sequenceName}\nprojecTag: {self.projectTag}\n"\
        f"projectDescription: {self.projectDescription}\nsubjectTag: {self.subjectTag}\nsessionTag: {self.sessionTag}\nspecies: {self.species}\n"\
        f"gender: {self.gender.name}\ntransferDate: {self.transferDate}\nageAtTransfer: {self.ageAtTransfer}\nsubjectDescription: {self.subjectDescription}\n"\
        f"weight: {self.weight}{self.weightUnit.name}\ntreatment: {self.treatment}\nscanTag: {self.scanTag}\nstudyType: {self.studyType}\n"\
        f"taskName: {self.taskName}\ntaskDescription: {self.taskDescription}\nusername: {self.username}\nacquisitionDate: {self.acquisitionDate}\n"\
        f"type: {self.type.name}\nstimulationToggleTimes: {self.stimulationToggleTimes}\nIcoScanVersion: {self.icoScanVersion}\n"
        return rep

class VoxDim:
    def __init__(self, dx, dy, dz, dt, dr, dtheta) -> None:
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.dt = dt
        self.dr = dr
        self.dtheta = dtheta
    
    def __repr__(self):
        ...
    def __str__(self) -> str:
        return f"\n\tdx: {self.dx}\n\tdy: {self.dy}\n\tdz: {self.dz}\n\tdt: {self.dt}\n\tdr: {self.dr}\n\tdtheta: {self.dtheta}\n"


class IcoScanVersion:
    def __init__(self, major, minor, patch) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch
    
    def __repr__(self):
        ...
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}\n\tmajor: {self.major}\n\tminor: {self.minor}\n\tpatch: {self.patch}"


class Dim6:


    class Dim6type(IntEnum):
        ClutterFiltering = 0,
        EnhancedDoppler = 1,
        VelocityBandFiltering = 2,
        BrainMaskedDoppler = 3

    class ClutterFiltering:
        class clutterFilterType(IntEnum):
            StaticSVD = 0,
            DynamicSVD = 1,
            Butterworth = 2

        def __init__(self, clutterFilter, clutterFilterWindowDuration,
                        clutterFilterCutoffLow, clutterFilterCutoffHigh) -> None:
            self.clutterFilter = self.clutterFilterType(clutterFilter)
            self.clutterFilterWindowDuration = clutterFilterWindowDuration
            self.clutterFilterCutoffLow = clutterFilterCutoffLow
            self.clutterFilterCutoffHigh = clutterFilterCutoffHigh

        def __repr__(self):
            ...
        def __str__(self) -> str:
            return f"\t\tClutter Filtering Type: {self.clutterFilter.name}\n\t\tWindow Duration: {self.clutterFilterWindowDuration}"\
            f"\n\t\tCutoff Low: {self.clutterFilterCutoffLow}\n\t\tCutoff High: {self.clutterFilterCutoffHigh}\n"

    class VelocityBandwidthFiltering:
        def __init__(self, velocityMin, velocityMax) -> None:
            self.velocityMin = velocityMin
            self.velocityMax = velocityMax

        def __repr__(self):
            ...
        def __str__(self) -> str:
            return f"\t\tVelocity Min: ${self.velocityMin}\n\t\tVelocity Max: ${self.velocityMax}\n"

    def __init__(self, elementCount) -> None:
        self.dim6: int = elementCount
        self.dim6element: set[tuple[Dim6.Dim6type, object]] = set()

    def __repr__(self):
        ...
    def __str__(self) -> str:
        rep = f"{self.dim6}"
        for dimElement in self.dim6element:
            rep += f"\n\t{dimElement[0].name}: \n{dimElement[1]}"
        return rep

class AcquisitionMode(IntEnum):
    _2DScan = 0
    _3DScan = 1
    _4DScan = 2
    _4DScanCustom = 3


class Probe:
    class ProbeType(IntEnum):
        Linear = 0
        MultiArray = 1
        RCA = 2
        Phased = 3
        Matrix = 4

    def __init__(self, name: str,
                 probeType: ProbeType,
                 probeCentralFrequency: float,
                 probePitch: float,
                 probeElevationAperture: float,
                 probeRadiusOfCurvature: float,
                 probeNumberOfElements: int,
                 probeModel: str) -> None:
        self.name = name
        self.probeType = probeType
        self.probeCentralFrequency = probeCentralFrequency
        self.probePitch = probePitch
        self.probeElevationAperture = probeElevationAperture
        self.probeRadiusOfCorvature = probeRadiusOfCurvature
        self.probeNumberOfElements = probeNumberOfElements
        self.probeModel = probeModel
    
    def __repr__(self):
        ...
    def __str__(self) -> str:
        return f"{self.name}\n\tprobeType: {self.probeType.name}\n\t"\
        f"probeCentralFrequency: {self.probeCentralFrequency}\n\t"\
        f"probePitch: {self.probePitch}\n\t"\
        f"probeElevationAperture: {self.probeElevationAperture}\n\t"\
        f"probeRadiusOfCurvature: {self.probeRadiusOfCorvature}\n\t"\
        f"probeNumberOfElements: {self.probeNumberOfElements}\n\t"\
        f"probeModel: {self.probeModel}"


class ProbeToLabElements:
    class ProbeToLabMatrices:
        def __init__(self, x, y, z) -> None:
            self.x = x
            self.y = y
            self.z = z
        def __repr__(self):
            ...
        def __str__(self) -> str:
            return f"\n\t\tx: {self.x}\n\t\ty: {self.y}\n\t\tz: {self.z}"
        

    def __init__(self, matricesCount) -> None:
        self.matricesCount = matricesCount
        self.matricesList: list[ProbeToLabElements.ProbeToLabMatrices] = []

    def __repr__(self):
        ...
    def __str__(self) -> str:
        rep = f"{self.matricesCount}"
        for i in range(len(self.matricesList)):
            rep += f"\n\t{i}: {self.matricesList[i]}"
        return rep

class Depth:
    def __init__(self, depthNear, depthFar) -> None:
        self.depthNear: float = depthNear
        self.depthFar: float = depthFar
    
    def __repr__(self):
        ...
    def __str__(self) -> str:
        return f"\n\tnear: {self.depthNear}\n\tfar: {self.depthFar}"
    
class GenderType(IntEnum):
    Undefined = 0
    Male = 1
    Female = 2
    Other = 3

class WeightUnitType(IntEnum):
    mg = 0
    g = 1
    kg = 2

class ScanType(IntEnum):
    Source = 0
    Proc = 1
