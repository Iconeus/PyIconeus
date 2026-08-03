from io import BufferedReader
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
    rotation_xyz,
    inverse_rotation_xyz,
)
from ..utils.consolidation import consolidate_scan

from ..models.Bps import Bps


class Scan:
    def __init__(self, filepath: str, is_binary: bool) -> None:
        """Scan class constructor. Reads the input file depending of the type set in 'is_binary'.
        For scans v1 (not binary), the scan is filled with a lot of default values, matching the v2 format.

        Parameters
        ----------
        **filepath**: str
            The file path for the scan
        **is_binary**: bool
            Boolean indicating the version of the scan

        Returns
        -------

        None

        """
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
        self.icoScanVersion: IcoScanVersion | None
        self.voxels: np.ndarray
        self.bps: Bps
        if is_binary:
            self.load_scan_binary(filepath)
        else:
            self.load_scan_hdf5(filepath)

    def load_scan_hdf5(self, filepath: str) -> None:
        """
        V1 scan loading function

        Parameters
        ----------

        **filepath**: str
            HDF5 file path of the scan

        Returns
        -------

        None
        """
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
            tmp = np.sort(acqMetaData["timeOriginal"][:], axis=0)
            dt = float(tmp[1][0] - tmp[0][0])
            dy = float(acqMetaData["voxDim"]["dy"][0][0])
            if not self.canBeConsolidated(f):
                self.nTime = acqMetaData["imgDim"]["nscanRepeat"][()][0][0]
                timeOriginal = acqMetaData["timeOriginal"][:]
                self.theoricalTimeIndices = np.round((timeOriginal - dt) / dt)
                probeToLabs = acqMetaData["probeToLab"][:]
                self.probeToLabsTranslations = ProbeToLabElements(len(probeToLabs))
                self.probeToLabsRotations = ProbeToLabElements(len(probeToLabs))
                translations = np.ndarray(shape=(len(probeToLabs), 3))
                rotations = np.ndarray(shape=(len(probeToLabs), 3))
                for i in range(len(probeToLabs)):
                    tform = probeToLabs[i]
                    tr = np.copy(tform.T[3][0:3])
                    tform.T[3][0:3] = 0
                    eul = inverse_rotation_xyz(tform)
                    rotations[i] = eul
                    translations[i] = tr
                    self.probeToLabsTranslations.setProbe2LabTransform(translations)
                    self.probeToLabsRotations.setProbe2LabTransform(rotations)
                self.sizeX: int = self.voxels.shape[0]
                self.sizeY: int = self.voxels.shape[1]
                self.sizeZ: int = self.voxels.shape[2]
                self.nTime: int = self.voxels.shape[3]
                self.nPose: int | Literal[1] = (
                    self.voxels.shape[4] if self.voxels.ndim > 4 else 1
                )
                if self.voxels.ndim < 6:
                    self.voxels = self.voxels.reshape(
                        (self.sizeX, self.sizeY, self.sizeZ, self.nTime, self.nPose, 1)
                    )
            else:
                (data, time, timeIndices, probeTranslation, probeRotation, dy) = (
                    consolidate_scan(f)
                )
                self.sizeX: int = data.shape[0]
                self.sizeY: int = data.shape[1]
                self.sizeZ: int = data.shape[2]
                self.nTime: int = data.shape[3]
                self.nPose: int | Literal[1] = data.shape[4] if data.ndim > 4 else 1
                if data.ndim < 6:
                    data = data.reshape(
                        (self.sizeX, self.sizeY, self.sizeZ, self.nTime, self.nPose, 1)
                    )
                self.probeToLabsTranslations = ProbeToLabElements(self.nPose)
                self.probeToLabsTranslations.setProbe2LabTransform(probeTranslation)
                self.probeToLabsRotations = ProbeToLabElements(self.nPose)
                self.probeToLabsRotations.setProbe2LabTransform(probeRotation)
                self.measuredTimes: list[float] = time.reshape(-1).tolist()
                self.theoricalTimeIndices = timeIndices.reshape(-1).tolist()
                self.voxels: np.ndarray = data
            self.integrationWindowDuration = float(acqMetaData["voxDim"]["dt"][0][0])
            self.voxDim = VoxDim()
            self.voxDim.load_hdf5(acqMetaData["voxDim"], dt, dy)
            self.fill_default(f)

    def matchAcquisitionMode(self, acqMetaData: h5py.Dataset) -> None:
        """
        HDF5 helper function to correctly set the scan's acquisition mode

        Parameters
        ----------

        **acqMetaData**: hdf5.Dataset
            The aqcuisition dataset

        Returns
        -------

        None
        """
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

    def fill_default(self, f: h5py.Group) -> None:
        """
        Fill all missing values for the HDF5 file with their respective default values

        Parameters
        ----------

        **f**: h5py.Dataset
            The root dataset of the file

        Returns
        -------

        None
        """
        self.dim6 = Dim6()
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
        dzIcoBright = np.trunc(
            1e8 * 1540 * 1e-6 / 12.5
        )  # Mean speed of sound propagation in soft tissus by the probe frequency
        dzIcoPrime = np.trunc(1e8 * 1540 * 1e-6 / 15.625)
        dzIcoRange = np.trunc(1e8 * 1540 * 1e-6 / 8.9290)
        dzIcoDeep = np.trunc(1e8 * 1540 * 1e-6 / 6.25)
        myTolerance: float = 2
        convertedDz = np.trunc(self.voxDim.dz * 1e8)
        if self.probe.probeType == Probe.ProbeType.MultiArray:
            self.probe.name = "IcoPrime 4D MultiArray"
        elif self.probe.probeType == Probe.ProbeType.RCA:
            if abs(convertedDz - dzIcoPrime) < myTolerance:
                self.probe.name = "IcoPrime 4D RCA"
            else:
                self.probe.name = "IcoBright 4D RCA"
        else:
            if abs(convertedDz - dzIcoRange) < myTolerance:
                self.probe.name = "IcoRange"
            elif abs(convertedDz - dzIcoDeep) < myTolerance:
                self.probe.name = "IcoDeep"
            elif abs(convertedDz - dzIcoBright) < myTolerance:
                self.probe.name = "IcoBright"
            elif abs(convertedDz - dzIcoPrime) < myTolerance:
                if self.sizeX == 128:
                    self.probe.name = "IcoPrime"
                elif self.sizeX == 192:
                    self.probe.name = "IcoPrimeXL"
                else:
                    self.probe.name = "IcoPrimeMini"
            else:
                self.probe.name = "unknown"
        self.probe.fill_default()
        self.ultrafastTransmitFrequency = 15.625
        self.ultrafastSamplingFrequency = 62.5
        self.planeWaveAngles: np.ndarray = np.arange(-10, 12, 2, dtype=float).tolist()
        if self.probe.name == "IcoPrime 4D MultiArray":
            self.planeWaveAngles: np.ndarray = np.linspace(-12, 12, 8).tolist()
        self.transmitVoltage = 25
        self.pulseRepetitionFrequency: int = len(self.planeWaveAngles) * 500
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

    def fillIcoScanVersion(self, neuroscan: str) -> None:
        """
        Fill the IcoScanVersion's class using the given string for HDF5 files

        Parameters
        ----------

        **neuroscan**: str
            HDF5 string of the IcoScan version

        Returns
        -------

        None
        """
        if neuroscan.startswith("Conexus Software version V"):
            major = int(neuroscan[-3])
            minor = int(neuroscan[-1])
            patch = 0
        elif neuroscan.startswith("IcoScan version"):
            major = int(neuroscan[-5])
            minor = int(neuroscan[-3])
            patch = int(neuroscan[-1])
        else:
            self.icoScanVersion = None
            return
        self.icoScanVersion = IcoScanVersion(major, minor, patch)

    def canBeConsolidated(self, hdf5_data: h5py.Dataset) -> bool:
        """
        Check consolidation requirements. If it cannot be consolidated, do the appropriate modification to the element based on the acquisition mode

        Parameters
        ----------

        **hdf5_data**: h5py.Dataset
            The HDF5 root dataset

        Returns
        -------
        bool
            Returns True if the scan can be consolidated, False otherwise
        """
        if (
            self.acquisitionMode == AcquisitionMode._4DscanRCA
            or self.acquisitionMode == AcquisitionMode._3DscanRCA
        ):
            data = hdf5_data["Data"][:].T
            time = hdf5_data["acqMetaData"]["theoricalTime"][:]
            self.measuredTimes = np.tile(time, (data.shape[1], 1)).tolist()
            self.probe.probeType = Probe.ProbeType.RCA
            self.voxels = data
            return False
        elif self.acquisitionMode == AcquisitionMode._4DScanCustom:
            data: np.ndarray = hdf5_data["Data"][:].T
            data = np.transpose(data, axes=(0, 1, 2, 5, 4, 3))
            blockRepeat: int = int(
                hdf5_data["acqMetaData"]["imgDim"]["nscanRepeat"][()][0][0]
            )
            nPose: int = int(hdf5_data["acqMetaData"]["imgDim"]["npose"][()][0][0])
            time = hdf5_data["acqMetaData"]["time"][:]
            self.measuredTimes = np.reshape(time, (nPose * blockRepeat)).tolist()
            self.probe.probeType = Probe.ProbeType.Linear
            self.voxels = data
            return False
        elif (
            hdf5_data["Data"][:].shape[1] == 4
            and hdf5_data["Data"][:].shape[4] == 1
            and self.acquisitionMode == AcquisitionMode._4DScan
        ):
            data = hdf5_data["Data"][:].T
            data = np.transpose(data, axes=(0, 3, 2, 5, 1, 6, 4))
            self.nPose = 4  # Size Y
            self.sizeY = 1
            self.measuredTimes = np.tile(
                hdf5_data["acqMetaData"][:], (1, self.nPose)
            ).tolist()
            self.probe.probeType = Probe.ProbeType.MultiArray
            self.voxels = data
            return False
        return True

    def load_scan_binary(self, filepath: str) -> None:
        """
        V2 scan loading function

        Parameters
        ----------

        **filepath**: str
            Binary file path of the scan

        Returns
        -------

        None
        """
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
                (
                    self.sizeX,
                    self.sizeY,
                    self.sizeZ,
                    self.nTime,
                    self.nPose,
                    self.dim6.count,
                ),
                order="F",  # Reshape in Fortran-like order, since MATLAB uses the same order
            )

    def get_VoxelToProbe(self) -> np.ndarray:
        """
        Compute the VoxelToProbe affine

        Parameters
        ----------

        None

        Returns
        -------

        np.ndarray (4, 4)
            The computed affine matrix
        """
        shift_voxel: np.ndarray = translationMatrix(-1, -1, -1)
        center_probe: np.ndarray = translationMatrix(
            (float)(-((self.sizeX - 1) / 2)), (float)(-((self.sizeY - 1) / 2)), 0
        )
        scale_to_metric: np.ndarray = scaleMatrix(
            self.voxDim.dx, self.voxDim.dy, -self.voxDim.dz
        )
        move_probe_up: np.ndarray = translationMatrix(
            0, 0, 0.001 * -self.depth.depthNear
        )
        return move_probe_up @ scale_to_metric @ center_probe @ shift_voxel

    def get_ProbeToLab(self) -> list[np.ndarray]:
        """
        Compute the ProbeToLabs matrices.
        One translation matrix per rotation: The translation represents the mean translation of the volume for a specific probe rotation

        Parameters
        ----------

        None

        Returns
        -------

        list[np.ndarray]
            list of affine matrix, one per rotation
        """
        rep = []
        for i in range(self.probeToLabsRotations.matricesCount):
            rot = (
                self.probeToLabsRotations.matricesList[i].x,
                self.probeToLabsRotations.matricesList[i].y,
                self.probeToLabsRotations.matricesList[i].z,
            )
            Rm = rotation_xyz(rot)
            Rm.T[3][0] = self.probeToLabsTranslations.matricesList[i].x
            Rm.T[3][1] = self.probeToLabsTranslations.matricesList[i].y
            Rm.T[3][2] = self.probeToLabsTranslations.matricesList[i].z
            rep.append(Rm)
        return rep

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

    __repr__ = __str__


class VoxDim:
    def __init__(self, dx=0, dy=0, dz=0, dt=0, dr=0, dtheta=0) -> None:
        self.dx: float = dx
        self.dy: float = dy
        self.dz: float = dz
        self.dt: float = dt
        self.dr: float = dr
        self.dtheta: float = dtheta

    def load_hdf5(self, voxDimData: h5py.Dataset, dt: float, dy: float | None) -> None:
        """
        Fill the VoxDim's class with the given dataset and values depending if the scan has been consolidated or not

        Parameters
        ----------

        **voxDimData**: h5py.Dataset
            The VoxDim dataset of the HDF5 file
        **dt**: float
            The computed dt value
        **dy**: float | None
            The computed value of dy, None if not consolidated

        Returns
        -------

        None
        """
        self.dx: float = float(voxDimData["dx"][0][0])
        if dy is None:
            self.dy: float = float(voxDimData["dy"][0][0])
        else:
            self.dy = dy
        self.dz: float = float(voxDimData["dz"][0][0])
        self.dt = dt

    def load_binary(self, f) -> None:
        """
        Fill the VoxDim's class with the given binary stream

        Parameters
        ----------

        **f**: BufferedReader
            The binary stream

        Returns
        -------

        None
        """
        self.dx = unpack("@d", f.read(8))[0]
        self.dy = unpack("@d", f.read(8))[0]
        self.dz = unpack("@d", f.read(8))[0]
        self.dt = unpack("@d", f.read(8))[0]
        self.dr = unpack("@d", f.read(8))[0]
        self.dtheta = unpack("@d", f.read(8))[0]

    def __str__(self) -> str:
        return f"\n\tdx: {self.dx}\n\tdy: {self.dy}\n\tdz: {self.dz}\n\tdt: {self.dt}\n\tdr: {self.dr}\n\tdtheta: {self.dtheta}\n"

    __repr__ = __str__


class IcoScanVersion:
    def __init__(self, major: int, minor: int, patch: int) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}\n\tmajor: {self.major}\n\tminor: {self.minor}\n\tpatch: {self.patch}"

    __repr__ = __str__


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

        def load_binary(self, f: BufferedReader) -> None:
            """
            ClutterFiltering's binary reader. Creates the correct Dim6 element with the given binary stream

            Parameters
            ----------

            **f**: BufferedReader
                The binary stream

            Returns
            -------

            None
            """
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

        def __str__(self) -> str:
            return (
                f"\t\tClutter Filtering Type: {self.clutterFilter.name}\n\t\tWindow Duration: {self.clutterFilterWindowDuration}"
                f"\n\t\tCutoff Low: {self.clutterFilterCutoffLow}\n\t\tCutoff High: {self.clutterFilterCutoffHigh}\n"
            )

        __repr__ = __str__

    class VelocityBandwidthFiltering:
        def __init__(self) -> None:
            self.velocityMin: float
            self.velocityMax: float

        def load_binary(self, f: BufferedReader) -> None:
            """
            VelocityBandwithFiltering's binary reader. Creates the correct Dim6 element with the given binary stream

            Parameters
            ----------

            **f**: BufferedReader
                The binary stream

            Returns
            -------

            None
            """
            self.velocityMin = unpack("@f", f.read(4))[0]
            self.velocityMax = unpack("@f", f.read(4))[0]
            f.seek(12, 1)

        def __str__(self) -> str:
            return f"\t\tVelocity Min: ${self.velocityMin}\n\t\tVelocity Max: ${self.velocityMax}\n"

        __repr__ = __str__

    def __init__(self) -> None:
        self.count: int
        self.dim6element: set[tuple[Dim6.Dim6Intent, object]] = set()

    def load_binary(self, f) -> None:
        """
        Dim6's binary reader. Creates the correct Dim6 element with the given binary stream

        Parameters
        ----------

        **f**: BufferedReader
            The binary stream

        Returns
        -------

        None
        """
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

    def __str__(self) -> str:
        rep = f"{self.count}"
        for dimElement in self.dim6element:
            rep += f"\n\t{dimElement[0].name}: \n{dimElement[1]}"
        return rep

    __repr__ = __str__


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

    def fill_default(self) -> None:
        """
        Fill the Probe class its default values

        Parameters
        ----------

        None

        Returns
        -------

        None
        """
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

    def load_binary(self, f: BufferedReader) -> None:
        """
        Probe's binary loader. Fills the Probe class with the given binary stream

        Parameters
        ----------

        **f**: BufferedReader
            The binary stream

        Returns
        -------

        None
        """
        self.probeType = self.ProbeType(unpack("@L", f.read(4))[0])
        self.probeCentralFrequency = unpack("@d", f.read(8))[0]
        self.probePitch = unpack("@d", f.read(8))[0]
        self.probeElevationAperture = unpack("@d", f.read(8))[0]
        f.seek(8, 1)
        self.probeRadiusOfCurvature = unpack("@d", f.read(8))[0]
        self.probeNumberOfElements = unpack("@H", f.read(2))[0]
        self.probeModel = read_string_binary(f, "@H", 2)
        self.name = read_string_binary(f, "@H", 2)

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

    __repr__ = __str__


class ProbeToLabElements:
    class ProbeToLabMatrices:
        def __init__(self, x: float, y: float, z: float) -> None:
            self.x = x
            self.y = y
            self.z = z

        def __str__(self) -> str:
            return f"\n\t\tx: {self.x}\n\t\ty: {self.y}\n\t\tz: {self.z}"

        __repr__ = __str__

    def __init__(self, matricesCount) -> None:
        self.matricesCount: int = matricesCount
        self.matricesList: list[self.ProbeToLabMatrices] = []

    def setProbe2LabTransform(self, transform: np.ndarray) -> None:
        """
        Set the given transform vector as the A ProbeToLab element (for HDF5 reader)

        Parameters
        ----------

        **transform**: np.ndarray
            The vector of 3 element of the translation/rotation matrix components

        Returns
        -------

        None
        """
        for t in transform:
            self.matricesList.append(
                self.ProbeToLabMatrices(float(t[0]), float(t[1]), float(t[2]))
            )

    def load_binary(self, f: BufferedReader) -> None:
        """
        Reads the ProbeToLab Translation/Rotation from the binary stream

        Parameters
        ----------

        **f**: BufferedReader
            The Binary stream

        Returns
        -------

        None
        """
        for _ in range(self.matricesCount):
            x = unpack("@d", f.read(8))[0]
            y = unpack("@d", f.read(8))[0]
            z = unpack("@d", f.read(8))[0]
            self.matricesList.append(ProbeToLabElements.ProbeToLabMatrices(x, y, z))

    def __str__(self) -> str:
        rep = f"{self.matricesCount}"
        for i in range(len(self.matricesList)):
            rep += f"\n\t{i}: {self.matricesList[i]}"
        return rep

    __repr__ = __str__


class Depth:
    def __init__(self) -> None:
        self.depthNear: float
        self.depthFar: float

    def fill_default(self, voxel2probe: np.ndarray, sizeZ: float) -> None:
        """
        Fill the default depths values

        Parameters
        ----------

        **voxel2probe**: np.ndarray
            The VoxelToProbe Matrix
        **sizeZ**: float
            The Z size of the acquisition

        Returns
        -------

        None
        """
        tmp: np.ndarray = transform_points_forward(voxel2probe, np.array([1, 1, 1]))
        self.depthNear = float(abs(tmp[2]) * 1e3)
        tmp = transform_points_forward(voxel2probe, np.array([1, 1, sizeZ]))
        self.depthFar = float(abs(tmp[2]) * 1e3)

    def __str__(self) -> str:
        return f"\n\tnear: {self.depthNear}\n\tfar: {self.depthFar}"

    __repr__ = __str__


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
