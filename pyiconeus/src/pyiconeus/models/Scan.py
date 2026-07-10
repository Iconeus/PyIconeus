from numpy.dtypes import DateTime64DType
import h5py
import pytz
import numpy as np
from typing import Literal
from struct import unpack
from datetime import datetime
from enum import IntEnum
from ..utils.utils import (
    translationMatrix,
    scaleMatrix,
    read_string_binary,
    hdf5_string_reader,
    transform_points_forward,
)
from ..utils.consolidation import consolidate_scan

from ..models.Bps import Bps


class Scan:
    def __init__(self, filepath: str, is_binary: bool) -> None:
        self.sizeX: int
        self.sizeY: int
        self.sizeZ: int
        self.nTime: int
        self.nPose: int
        self.measuredTimes: list[float] = []
        self.theoricalTimeIndices: list[int] = []
        self.probeToLabsTranslations: ProbeToLabElements
        self.probeToLabsRotations: ProbeToLabElements
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
        self.transferDate: datetime
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
        self.acquisitionDate: datetime
        self.type: ScanType
        self.stimulationToggleTimes: list[float] = []
        self.icoScanVersion: IcoScanVersion
        self.voxels: np.ndarray
        self.bps: Bps
        if is_binary:
            self.load_scan_binary(filepath)
        else:
            self.load_scan_hdf5(filepath)

    def load_scan_hdf5(self, filepath) -> None:
        with h5py.File(filepath, "r") as f:
            metaData: h5py.Dataset = f["scanMetaData"]
            date_str: str = hdf5_string_reader(metaData["Date"])
            self.probe = Probe()
            date: datetime = datetime.strptime(
                date_str if date_str else "1970-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"
            )
            self.acquisitionDate = date.replace(tzinfo=pytz.utc)
            self.projectTag = hdf5_string_reader(metaData["Project_tag"])
            self.scanTag = hdf5_string_reader(metaData["Scan_tag"])
            self.subjectTag = hdf5_string_reader(metaData["Subject_tag"])
            self.sessionTag = hdf5_string_reader(metaData["Session_tag"])
            type: str = hdf5_string_reader(metaData["Type"])
            self.type = ScanType.Source if type == "source" else ScanType.Proc
            self.username = hdf5_string_reader(metaData["User_name"])
            self.projectDescription = hdf5_string_reader(metaData["Comment"])
            acqMetaData: h5py.Dataset = f["acqMetaData"]
            self.matchAcquisitionMode(acqMetaData)
            self.voxDim = VoxDim()
            self.voxDim.load_hdf5(acqMetaData["voxDim"])
            (data, time, timeIndices, probeTranslation, probeRotation) = (
                consolidate_scan(f)
            )
            self.sizeX: int = data.shape[0]
            self.sizeY: int = data.shape[1]
            self.sizeZ: int = data.shape[2]
            self.nTime: int = data.shape[3]
            self.nPose: int | Literal[1] = data.shape[4] if data.ndim > 4 else 1
            self.probeToLabsTranslations = ProbeToLabElements(self.nPose)
            self.probeToLabsTranslations.setProbe2LabTransform(probeTranslation)
            self.probeToLabsRotations = ProbeToLabElements(self.nPose)
            self.probeToLabsRotations.setProbe2LabTransform(probeRotation)
            self.measuredTimes: list[float] = time.reshape(-1).tolist()
            self.theoricalTimeIndices = timeIndices.reshape(-1).tolist()
            self.voxels: np.ndarray = data
            self.fill_default(f)

    def matchAcquisitionMode(self, acqMetaData: h5py.Dataset):
        _acquisitionMode = hdf5_string_reader(acqMetaData["acquisitionMode"])
        match _acquisitionMode:
            case "2Dscan":
                self.acquisitionMode = AcquisitionMode._2DScan
                self.probe.probeType = Probe.ProbeType.Linear
            case "3Dscan":
                self.acquisitionMode = AcquisitionMode._3DScan
                if acqMetaData["imgDim"]["npose"][()] == 4:
                    self.probe.probeType = Probe.ProbeType.MultiArray
                else:
                    self.probe.probeType = Probe.ProbeType.Linear
            case "4Dscan":
                self.acquisitionMode = AcquisitionMode._4DScan
                if acqMetaData["imgDim"]["npose"][()] == 4:
                    self.probe.probeType = Probe.ProbeType.MultiArray
                elif (
                    acqMetaData["imgDim"]["npose"][()] == 1
                    and acqMetaData["imgDim"]["sizeY"][()] == 4
                ):
                    self.probe.probeType = Probe.ProbeType.MultiArray
                else:
                    self.probe.probeType = Probe.ProbeType.Linear
            case "4DscanCustom":
                self.acquisitionMode = AcquisitionMode._4DScanCustom
                self.probe.probeType = Probe.ProbeType.Linear
            case "4DscanRCA":
                self.acquisitionMode = AcquisitionMode._4DscanRCA
                self.probe.probeType = Probe.ProbeType.RCA
            case "3DscanRCA":
                self.acquisitionMode = AcquisitionMode._3DscanRCA
                self.probe.probeType = Probe.ProbeType.RCA

    def fill_default(self, f: h5py.Group):
        self.dim6 = Dim6()
        self.integrationWindowDuration = float(
            f["acqMetaData"]["voxDim"]["dt"][()][0][0]
        )
        self.dim6.count = 1
        clutDefault = Dim6.ClutterFiltering()
        clutDefault.clutterFilter = Dim6.ClutterFiltering.clutterFilterType.StaticSVD
        clutDefault.clutterFilterCutoffHigh = 0
        clutDefault.clutterFilterCutoffLow = 0
        clutDefault.clutterFilterWindowDuration = self.integrationWindowDuration
        self.dim6.dim6element.add((Dim6.Dim6Intent.ClutterFiltering, clutDefault))
        self.depth = Depth()
        voxel2Probe = f["acqMetaData"]["voxelsToProbe"][:]
        self.depth.fill_default(voxel2Probe, self.sizeZ)
        dzIcoBright = np.trunc(1e8 * 1540 * 1e-6 / 12.5)
        dzRCA12 = dzIcoBright
        dzIcoPrime = np.trunc(1e8 * 1540 * 1e-6 / 15.625)
        dzRCA15 = dzIcoPrime
        dzIcoRange = np.trunc(1e8 * 1540 * 1e-6 / 8.9290)
        dzIcoDeep = np.trunc(1e8 * 1540 * 1e-6 / 6.25)
        myTolerance: float = 2
        convertedDz = np.trunc(f["acqMetaData"]["voxDim"]["dz"][()][0][0] * 1e8)
        if self.probe.probeType == Probe.ProbeType.MultiArray:
            self.probe.name = "IcoPrime 4D MultiArray"
        elif self.probe.probeType == Probe.ProbeType.RCA:
            if abs(convertedDz - dzRCA15) < myTolerance:
                self.probe.name = "IcoPrime 4D RCA"
            else:
                self.probe.name = "IcoBright 4D RCA"
        else:
            if abs(convertedDz - dzIcoRange) < myTolerance:
                self.probe.name = "IcoRange"
            elif abs(convertedDz - dzIcoDeep) < myTolerance:
                self.probe.name = "IcoDeep"
            elif abs(convertedDz - dzRCA12) < myTolerance:
                self.probe.name = "IcoBright"
            elif abs(convertedDz - dzIcoPrime) < myTolerance:
                sizeX = f["acqMetaData"]["imgDim"]["sizeX"][()][0][0]
                if sizeX == 128:
                    self.probe.name = "IcoPrime"
                elif sizeX == 192:
                    self.probe.name = "IcoPrimeXL"
                else:
                    self.probe.name = "IcoPrimeMini"
            else:
                self.probe.name = "unknown"
        self.probe.fill_default()
        self.ultrafastTransmitFrequency = 15.625
        self.ultrafastSamplingFrequency = 62.5
        self.planeWaveAngles = np.linspace(-10, 2, 10).tolist()
        if self.probe.name == "IcoPrime 4D MultiArray":
            self.planeWaveAngles = np.linspace(-12, 12, 8).tolist()
        self.transmitVoltage = 25
        self.pulseRepetitionFrequency = len(self.planeWaveAngles) * 500
        self.isMultiplane = False
        self.delayAfterTrigger = 0
        self.sequenceName = "default sequence"

        # Scan Meta Data
        refDate = datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc)
        self.gender = GenderType.Undefined
        self.projectDescription = hdf5_string_reader(f["scanMetaData"]["Comment"])
        self.species = "Unknown"
        self.transferDate = refDate
        self.ageAtTransfer = 0
        self.subjectDescription = "none"
        self.weightUnit = WeightUnitType.mg
        self.weight = 0
        self.treatment = ""
        self.studyType = ""
        self.taskName = ""
        self.taskDescription = "none"
        self.stimulationToggleTimes = []
        self.fillIcoScanVersion(
            hdf5_string_reader(f["scanMetaData"]["Neuroscan_version"])
        )

    def fillIcoScanVersion(self, neuroscan: str):
        if neuroscan.startswith("Conexus Software version V"):
            major = int(neuroscan[-3])
            minor = int(neuroscan[-1])
            patch = 0
        elif neuroscan.startswith("IcoScan version"):
            major = int(neuroscan[-5])
            minor = int(neuroscan[-3])
            patch = int(neuroscan[-1])
        else:
            major = 1
            minor = 0
            patch = 0
        self.icoScanVersion = IcoScanVersion(major, minor, patch)

    def load_scan_binary(self, filepath) -> None:
        with open(filepath, "rb") as f:
            f.seek(32)
            dO: int = unpack("@Q", f.read(8))[0]
            f.seek(92)
            self.sizeX = unpack("@Q", f.read(8))[0]
            self.sizeY = unpack("@Q", f.read(8))[0]
            self.sizeZ = unpack("@Q", f.read(8))[0]
            self.nTime = unpack("@Q", f.read(8))[0]
            self.nPose = unpack("@Q", f.read(8))[0]
            self.dim6 = Dim6()
            self.dim6.load_binary(f)
            self.voxDim = VoxDim()
            self.voxDim.load_binary(f)
            timeArraySize: int = self.sizeY * self.nTime * self.nPose
            for _ in range(timeArraySize):
                self.measuredTimes.append(unpack("@d", f.read(8))[0])
            for _ in range(timeArraySize):
                self.theoricalTimeIndices.append(unpack("@L", f.read(4))[0])
            self.probeToLabsTranslations = ProbeToLabElements(self.nPose)
            self.probeToLabsTranslations.load_binary(f)
            self.probeToLabsRotations = ProbeToLabElements(self.nPose)
            self.probeToLabsRotations.load_binary(f)
            f.seek(4, 1)
            self.acquisitionMode = AcquisitionMode(unpack("@L", f.read(4))[0])
            f.seek(4, 1)
            self.probe = Probe()
            self.probe.load_binary(f)
            depthNear = unpack("@d", f.read(8))[0]
            depthFar = unpack("@d", f.read(8))[0]
            self.depth = Depth()
            self.depth.depthNear = depthNear
            self.depth.depthFar = depthFar
            self.ultrafastTransmitFrequency = unpack("@d", f.read(8))[0]
            self.pulseRepetitionFrequency = unpack("@d", f.read(8))[0]
            self.ultrafastSamplingFrequency = unpack("@d", f.read(8))[0]
            f.seek(8, 1)
            nPlaneWavesAngles = unpack("@L", f.read(4))[0]
            for _ in range(nPlaneWavesAngles):
                self.planeWaveAngles.append(unpack("@d", f.read(8))[0])
            tempVal = unpack("@L", f.read(4))
            f.seek(tempVal[0] * 24 + 8, 1)
            self.transmitVoltage = unpack("@d", f.read(8))[0]
            f.seek(4, 1)
            self.delayAfterTrigger = unpack("@d", f.read(8))[0]
            tempVal = unpack("@L", f.read(4))
            f.seek(tempVal[0] * 8, 1)
            self.isMultiplane = unpack("@?", f.read(1))[0]
            f.seek(1, 1)
            self.integrationWindowDuration = unpack("@d", f.read(8))[0]
            self.sequenceName = read_string_binary(f, "@L", 4)
            self.projectTag = read_string_binary(f, "@L", 4)
            self.projectDescription = read_string_binary(f, "@L", 4)
            self.subjectTag = read_string_binary(f, "@L", 4)
            self.sessionTag = read_string_binary(f, "@L", 4)
            self.species = read_string_binary(f, "@L", 4)
            self.gender = GenderType(unpack("@L", f.read(4))[0])
            self.transferDate = datetime.fromtimestamp(
                unpack("@q", f.read(8))[0], pytz.utc
            )
            self.ageAtTransfer = unpack("@Q", f.read(8))[0]
            self.subjectDescription = read_string_binary(f, "@L", 4)
            self.weightUnit = WeightUnitType(unpack("@L", f.read(4))[0])
            self.weight = unpack("@f", f.read(4))[0]
            self.treatment = read_string_binary(f, "@L", 4)
            self.scanTag = read_string_binary(f, "@L", 4)
            self.studyType = read_string_binary(f, "@L", 4)
            self.taskName = read_string_binary(f, "@L", 4)
            self.taskDescription = read_string_binary(f, "@L", 4)
            self.username = read_string_binary(f, "@L", 4)
            for _ in range(2):
                tempVal = unpack("@L", f.read(4))[0]
                f.seek(tempVal, 1)
            self.acquisitionDate = datetime.fromtimestamp(
                unpack("@q", f.read(8))[0], pytz.utc
            )
            self.type = ScanType(unpack("@L", f.read(4))[0])
            toggleTimes: int = unpack("@L", f.read(4))[0]
            for _ in range(toggleTimes):
                self.stimulationToggleTimes.append(unpack("@f", f.read(4))[0])
            icoScanMajor = unpack("@L", f.read(4))[0]
            icoScanMinor = unpack("@L", f.read(4))[0]
            icoScanPatch = unpack("@L", f.read(4))[0]
            self.icoScanVersion = IcoScanVersion(
                icoScanMajor, icoScanMinor, icoScanPatch
            )
            f.seek(dO)
            dataSize = (
                self.sizeX
                * self.sizeY
                * self.sizeZ
                * self.nTime
                * self.nPose
                * self.dim6.count
            )
            self.voxels = np.fromfile(f, dtype="d", count=dataSize)
            self.voxels = self.voxels.reshape(
                (self.dim6.count, self.nTime, self.sizeZ, self.sizeY, self.sizeX),
                order="C",
            )

    def get_VoxelToProbe(self) -> np.ndarray:
        shift_voxel: np.ndarray = translationMatrix(-1, -1, -1)
        center_probe: np.ndarray = translationMatrix(
            (float)(-((self.sizeX - 1) / 2)), (float)(-((self.sizeY - 1) / 2)), 0
        )
        scale_to_metric: np.ndarray = scaleMatrix(
            self.voxDim.dx, self.voxDim.dy, -self.voxDim.dz
        )
        move_probe_up: np.ndarray = translationMatrix(
            0, 0, -self.depth.depthNear * 0.001
        )
        return move_probe_up @ scale_to_metric @ center_probe @ shift_voxel

    def __repr__(self): ...
    def __str__(self) -> str:
        rep = (
            f"sizeX: {self.sizeX}\nsizeY: {self.sizeY}\nsizeZ: {self.sizeZ}\nnTime: {self.nTime}\nnPose: {self.nPose}"
            f"\ndim6: {self.dim6}\nvoxDim: {self.voxDim}\nmeasuredTimes: {len(self.measuredTimes)} ({self.sizeY} * {self.nTime} * {self.nPose}) (sizeY * nTime * nPose)\n"
            f"theoricalTimeIndices: {len(self.theoricalTimeIndices)} ({self.sizeY} * {self.nTime} * {self.nPose}) (sizeY * nTime * nPose)\n"
            f"probeToLabsTranslation: {self.probeToLabsTranslations}\nprobeToLabsRotations: {self.probeToLabsRotations}\n"
            f"acquisitionMode: {self.acquisitionMode.name[1:]}\nprobe: {self.probe}\ndepth: {self.depth}\n"
            f"ultrafastTransmitFrequency: {self.ultrafastTransmitFrequency}\npulseRepetitionFrequency: {self.pulseRepetitionFrequency}\n"
            f"ultrafastSamplingFrequency: {self.ultrafastSamplingFrequency}\nplaneWavesAngles: {len(self.planeWaveAngles)}\n"
        )
        for i in range(len(self.planeWaveAngles)):
            rep += f"\t{i}: {self.planeWaveAngles[i]}\n"
        rep += (
            f"transmitVoltage: {self.transmitVoltage}\ndelayAfterTrigger: {self.delayAfterTrigger}\nisMultiplane: {self.isMultiplane}\n"
            f"integrationWindowDuration: {self.integrationWindowDuration}\nsequenceName: {self.sequenceName}\nprojecTag: {self.projectTag}\n"
            f"projectDescription: {self.projectDescription}\nsubjectTag: {self.subjectTag}\nsessionTag: {self.sessionTag}\nspecies: {self.species}\n"
            f"gender: {self.gender.name}\ntransferDate: {self.transferDate}\nageAtTransfer: {self.ageAtTransfer}\nsubjectDescription: {self.subjectDescription}\n"
            f"weight: {self.weight}{self.weightUnit.name}\ntreatment: {self.treatment}\nscanTag: {self.scanTag}\nstudyType: {self.studyType}\n"
            f"taskName: {self.taskName}\ntaskDescription: {self.taskDescription}\nusername: {self.username}\nacquisitionDate: {self.acquisitionDate}\n"
            f"type: {self.type.name}\nstimulationToggleTimes: {self.stimulationToggleTimes}\nIcoScanVersion: {self.icoScanVersion}\n"
        )
        return rep


class VoxDim:
    def __init__(self, dx=0, dy=0, dz=0, dt=0, dr=0, dtheta=0) -> None:
        self.dx: float = dx
        self.dy: float = dy
        self.dz: float = dz
        self.dt: float = dt
        self.dr: float = dr
        self.dtheta: float = dtheta

    def load_hdf5(self, voxDimData: h5py.Dataset) -> None:
        self.dx: float = voxDimData["dx"][0]
        self.dy: float = voxDimData["dy"][0]
        self.dz: float = voxDimData["dz"][0]
        self.dt: float = voxDimData["dt"][0]

    def load_binary(self, f) -> None:
        self.dx = unpack("@d", f.read(8))[0]
        self.dy = unpack("@d", f.read(8))[0]
        self.dz = unpack("@d", f.read(8))[0]
        self.dt = unpack("@d", f.read(8))[0]
        self.dr = unpack("@d", f.read(8))[0]
        self.dtheta = unpack("@d", f.read(8))[0]

    def __repr__(self): ...
    def __str__(self) -> str:
        return f"\n\tdx: {self.dx}\n\tdy: {self.dy}\n\tdz: {self.dz}\n\tdt: {self.dt}\n\tdr: {self.dr}\n\tdtheta: {self.dtheta}\n"


class IcoScanVersion:
    def __init__(self, major: int, minor: int, patch: int) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch

    def __repr__(self): ...
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}\n\tmajor: {self.major}\n\tminor: {self.minor}\n\tpatch: {self.patch}"


class Dim6:
    class Dim6Intent(IntEnum):
        ClutterFiltering = (0,)
        EnhancedDoppler = (1,)
        VelocityBandFiltering = (2,)
        BrainMaskedDoppler = 3

    class ClutterFiltering:
        class clutterFilterType(IntEnum):
            StaticSVD = (0,)
            DynamicSVD = (1,)
            Butterworth = 2

        def __init__(self) -> None:
            self.clutterFilter: self.clutterFilterType
            self.clutterFilterWindowDuration: float
            self.clutterFilterCutoffLow: float
            self.clutterFilterCutoffHigh: float

        def load_binary(self, f) -> None:
            self.clutterFilter = self.clutterFilterType(unpack("@L", f.read(4))[0])
            self.clutterFilterWindowDuration = unpack("@d", f.read(8))[0]
            if (
                self.clutterFilter == self.clutterFilterType.StaticSVD
                or self.clutterFilter == self.clutterFilterType.DynamicSVD
            ):
                self.clutterFilterCutoffLow = unpack("@L", f.read(4))[0]
                self.clutterFilterCutoffHigh = unpack("@L", f.read(4))[0]
            else:
                self.clutterFilterCutoffLow = unpack("@f", f.read(4))[0]
                self.clutterFilterCutoffHigh = unpack("@f", f.read(4))[0]

        def __repr__(self): ...
        def __str__(self) -> str:
            return (
                f"\t\tClutter Filtering Type: {self.clutterFilter.name}\n\t\tWindow Duration: {self.clutterFilterWindowDuration}"
                f"\n\t\tCutoff Low: {self.clutterFilterCutoffLow}\n\t\tCutoff High: {self.clutterFilterCutoffHigh}\n"
            )

    class VelocityBandwidthFiltering:
        def __init__(self) -> None:
            self.velocityMin: float
            self.velocityMax: float

        def load_binary(self, f) -> None:
            self.velocityMin = unpack("@f", f.read(4))[0]
            self.velocityMax = unpack("@f", f.read(4))[0]
            f.seek(12, 1)

        def __repr__(self): ...
        def __str__(self) -> str:
            return f"\t\tVelocity Min: ${self.velocityMin}\n\t\tVelocity Max: ${self.velocityMax}\n"

    def __init__(self) -> None:
        self.count: int
        self.dim6element: set[tuple[Dim6.Dim6Intent, object]] = set()

    def load_binary(self, f) -> None:
        self.count = unpack("@Q", f.read(8))[0]
        dim6intents: list[int] = []
        for _ in range(self.count):
            dim6intents.append(unpack("@L", f.read(4))[0])
        for intent in dim6intents:
            if (
                intent == self.Dim6Intent.EnhancedDoppler
                or intent == self.Dim6Intent.BrainMaskedDoppler
            ):
                f.seek(20, 1)
            elif intent == self.Dim6Intent.ClutterFiltering:
                clutterFiltering = self.ClutterFiltering()
                self.dim6element.add(
                    (self.Dim6Intent.ClutterFiltering, clutterFiltering.load_binary(f))
                )
            elif intent == self.Dim6Intent.VelocityBandFiltering:
                velocityBandWidth = self.VelocityBandwidthFiltering()
                self.dim6element.add(
                    (
                        self.Dim6Intent.VelocityBandFiltering,
                        velocityBandWidth.load_binary(f),
                    )
                )

    def __repr__(self): ...
    def __str__(self) -> str:
        rep = f"{self.count}"
        for dimElement in self.dim6element:
            rep += f"\n\t{dimElement[0].name}: \n{dimElement[1]}"
        return rep


class AcquisitionMode(IntEnum):
    _2DScan = 0
    _3DScan = 1
    _4DScan = 2
    _4DScanCustom = 3
    _4DscanRCA = 4
    _3DscanRCA = 5


class Probe:
    class ProbeType(IntEnum):
        Linear = 0
        MultiArray = 1
        RCA = 2
        Phased = 3
        Matrix = 4

    def __init__(self) -> None:
        self.name: str
        self.probeType: self.ProbeType
        self.probeCentralFrequency: float
        self.probePitch: float
        self.probeElevationAperture: float
        self.probeRadiusOfCurvature: float
        self.probeNumberOfElements: float
        self.probeModel: str

    def fill_default(
        self,
    ):
        if (
            self.name == "IcoPrime"
            or self.name == "unknown"
            or self.name == "IcoPrime 4D MultiArray"
        ):
            self.probeCentralFrequency = 15.625
            self.probePitch = 0.11
            self.probeElevationAperture = 1.5
            self.probeNumberOfElements = 128
            self.probeModel = "2392"
            if self.name == "IcoPrime 4D MultiArray":
                self.probeNumberOfElements = 256
                self.probeModel = "2390"
        self.probeRadiusOfCurvature = 0

    def load_binary(self, f) -> None:
        self.probeType = self.ProbeType(unpack("@L", f.read(4))[0])
        self.probeCentralFrequency = unpack("@d", f.read(8))[0]
        self.probePitch = unpack("@d", f.read(8))[0]
        self.probeElevationAperture = unpack("@d", f.read(8))[0]
        f.seek(8, 1)
        self.probeRadiusOfCurvature = unpack("@d", f.read(8))[0]
        self.probeNumberOfElements = unpack("@H", f.read(2))[0]
        self.probeModel = read_string_binary(f, "@H", 2)
        self.name = read_string_binary(f, "@H", 2)

    def __repr__(self): ...
    def __str__(self) -> str:
        return (
            f"{self.name}\n\tprobeType: {self.probeType.name}\n\t"
            f"probeCentralFrequency: {self.probeCentralFrequency}\n\t"
            f"probePitch: {self.probePitch}\n\t"
            f"probeElevationAperture: {self.probeElevationAperture}\n\t"
            f"probeRadiusOfCurvature: {self.probeRadiusOfCurvature}\n\t"
            f"probeNumberOfElements: {self.probeNumberOfElements}\n\t"
            f"probeModel: {self.probeModel}"
        )


class ProbeToLabElements:
    class ProbeToLabMatrices:
        def __init__(self, x: float, y: float, z: float) -> None:
            self.x = x
            self.y = y
            self.z = z

        def __repr__(self): ...
        def __str__(self) -> str:
            return f"\n\t\tx: {self.x}\n\t\ty: {self.y}\n\t\tz: {self.z}"

    def __init__(self, matricesCount) -> None:
        self.matricesCount: int = matricesCount
        self.matricesList: list[self.ProbeToLabMatrices] = []

    def setProbe2LabTransform(self, transform: np.ndarray) -> None:
        for t in transform:
            self.matricesList.append(
                self.ProbeToLabMatrices(float(t[0]), float(t[1]), float(t[2]))
            )

    def load_binary(self, f) -> None:
        for _ in range(self.matricesCount):
            x = unpack("@d", f.read(8))[0]
            y = unpack("@d", f.read(8))[0]
            z = unpack("@d", f.read(8))[0]
            self.matricesList.append(ProbeToLabElements.ProbeToLabMatrices(x, y, z))

    def __repr__(self): ...
    def __str__(self) -> str:
        rep = f"{self.matricesCount}"
        for i in range(len(self.matricesList)):
            rep += f"\n\t{i}: {self.matricesList[i]}"
        return rep


class Depth:
    def __init__(self) -> None:
        self.depthNear: float
        self.depthFar: float

    def fill_default(self, voxel2probe: np.ndarray, sizeZ: float):
        tmp: np.ndarray = transform_points_forward(voxel2probe, np.array([1, 1, 1]))
        self.depthNear = float(abs(tmp[2]) * 1e3)
        tmp = transform_points_forward(voxel2probe, np.array([1, 1, sizeZ]))
        self.depthFar = float(abs(tmp[2]) * 1e3)

    def __repr__(self): ...
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
