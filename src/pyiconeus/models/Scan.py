# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import os
import re
from datetime import datetime
from enum import IntEnum
from io import BufferedReader

import h5py
import numpy as np
import pytz

from ..models.Bps import Bps
from ..utils.consolidation import consolidate_scan, theoretical_time_indices
from ..utils.utils import (
    _read_struct,
    hdf5_string_reader,
    inverse_rotation_xyz,
    read_string_binary,
    rotation_xyz,
    scale_matrix,
    transform_points_forward,
    translation_matrix,
)


class Scan:
    """IcoScan acquisition scan model (v1 HDF5 or v2 binary).

    Reads, parses, and exposes metadata + voxel data from IcoScan scan files.
    The ``open_path`` dispatcher auto-detects the file format from its extension.

    Attributes
    ----------
    sizeX, sizeY, sizeZ : int
        Spatial dimensions of the voxel grid.
    nTime : int
        Number of time frames per probe pose.
    nPose : int
        Number of probe poses.
    measuredTimes : list[float]
        Measured timestamps for each frame/pose combination.
    theoreticalTimeIndices : list[int]
        Theoretical (0-indexed) time indices computed from measured times.
    probeToLabsTranslations : np.ndarray
        Translation vectors for each probe pose, shape ``(nPose, 3)``.
    probeToLabsRotations : np.ndarray
        Euler angle rotations (x, y, z in radians) for each probe pose, shape ``(nPose, 3)``.
    dim6 : Dim6
        Dimensionality-6 processing options.
    voxDim : VoxDim
        Voxel and frame spacing information.
    acquisitionMode : AcquisitionMode
        Type of the acquired scan.
    probe : Probe
        Information about the ultrasound probe used.
    depth : Depth
        Near and far depth values.
    ultrafastTransmitFrequency : float
        Ultrafast transmit frequency in MHz.
    pulseRepetitionFrequency : float
        Pulse repetition frequency in kHz.
    ultrafastSamplingFrequency : float
        Sampling frequency of the raw channel data.
    planeWaveAngles : list[float]
        Plane wave angles used in the acquisition (degrees).
    transmitVoltage : float
        Transmit voltage in volts.
    delayAfterTrigger : float
        Delay after trigger, seconds.
    isMultiplane : bool
        Whether multi-plane imaging was used.
    integrationWindowDuration : float
        Integration window duration, seconds.
    sequenceName : str
        Ultrasound sequence name.
    projectTag, subjectTag, sessionTag, scanTag : str
        Identifying tags for the project and subject.
    projectDescription : str
        User comment / description of the acquisition.
    species : str
        Species of the subject (e.g., "Mouse").
    gender : GenderType
        Subject gender enum.
    transferDate, acquisitionDate : datetime
        Dates when data was acquired and transferred.
    ageAtTransfer : int
        Age at data transfer in days.
    weight : float
        Subject weight.
    weightUnit : WeightUnitType
        Unit of the subject weight.
    treatment : str
        Treatment description.
    studyType, taskName, taskDescription : str
        Experimental context metadata.
    username : str
        User who performed the acquisition.
    type : ScanType
        Whether this is a source or processed scan.
    stimulationToggleTimes : list[float]
        Times of external stimulation toggles (seconds).
    icoScanVersion : IcoScanVersion | None
        Version of the IcoScan software that acquired the data.
    voxels : np.ndarray
        The voxel data, typically ``(sizeX, sizeY, sizeZ, nTime, nPose, dim6.count)``.
    bps : Bps | None
        Optional Brain-to-Lab affine transform.
    """

    def __init__(self, filepath: str | os.PathLike[str], is_binary: bool) -> None:
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
        self.theoreticalTimeIndices: list[int] = []
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
        self.icoScanVersion: IcoScanVersion | None = None
        self.voxels: np.ndarray
        self.bps: Bps | None = None
        if is_binary:
            self.load_scan_binary(filepath)
        else:
            self.load_scan_hdf5(filepath)

    def load_scan_hdf5(self, filepath: str | os.PathLike[str]) -> None:
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
            acqMetaData = self._load_hdf5_metadata(f)
            dt, dy = self._load_hdf5_data(f, acqMetaData)
            self.integrationWindowDuration = float(acqMetaData["voxDim"]["dt"][0][0])
            self.voxDim = VoxDim()
            self.voxDim.load_hdf5(acqMetaData["voxDim"], dt, dy)
            self.fill_default(f)

    def _load_hdf5_data(
        self, f: h5py.File, acqMetaData: h5py.Dataset
    ) -> tuple[float, float | None]:
        """Load HDF5 voxels, timings, and probe transforms."""
        time_original = np.asarray(acqMetaData["timeOriginal"][:]).reshape(-1)
        integration_time = float(acqMetaData["voxDim"]["dt"][0][0])
        dt = (
            float(np.diff(np.sort(time_original))[0])
            if time_original.size > 1
            else integration_time
        )
        if dt == 0:
            dt = integration_time
        dy: float | None = float(acqMetaData["voxDim"]["dy"][0][0])
        if not self.can_be_consolidated(f):
            self._load_nonconsolidated_data(f)
            self.nPose = self.voxels.shape[4] if self.voxels.ndim > 4 else 1
            self.nTime = acqMetaData["imgDim"]["nscanRepeat"][()][0][0]
            timeOriginal = acqMetaData["timeOriginal"][:]
            self.theoreticalTimeIndices = theoretical_time_indices(
                timeOriginal, dt, dt
            ).tolist()
            probeToLabs = acqMetaData["probeToLab"][:]
            if probeToLabs.ndim < 3:
                probeToLabs = probeToLabs.reshape((1, 4, 4))
            translations: np.ndarray = np.ndarray(shape=(len(probeToLabs), 3))
            rotations: np.ndarray = np.ndarray(shape=(len(probeToLabs), 3))
            for i in range(len(probeToLabs)):
                tform = probeToLabs[i]
                tr = np.copy(tform.T[3][0:3])
                tform.T[3][0:3] = 0
                eul = inverse_rotation_xyz(tform)
                rotations[i] = eul
                translations[i] = tr
            self.probeToLabsTranslations = translations
            self.probeToLabsRotations = rotations
            self.sizeX = self.voxels.shape[0]
            self.sizeY = self.voxels.shape[1]
            self.sizeZ = self.voxels.shape[2]
            self.nTime = self.voxels.shape[3]
        else:
            data, time, timeIndices, probeTranslation, probeRotation, dy = (
                consolidate_scan(f)
            )
            self.sizeX, self.sizeY, self.sizeZ, self.nTime = data.shape[:4]
            self.nPose = data.shape[4] if data.ndim > 4 else 1
            if data.ndim < 6:
                data = data.reshape(
                    (self.sizeX, self.sizeY, self.sizeZ, self.nTime, self.nPose, 1)
                )
            self.probeToLabsTranslations = probeTranslation
            self.probeToLabsRotations = probeRotation
            self.measuredTimes = time.reshape(-1).tolist()
            self.theoreticalTimeIndices = timeIndices.reshape(-1).tolist()
            self.voxels = data
        return dt, dy

    def _load_hdf5_metadata(self, f: h5py.File) -> h5py.Dataset:
        """Load scan metadata and return the acquisition metadata group."""
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
        scan_type: str = hdf5_string_reader(metaData["Type"])
        if scan_type == "source":
            self.type = ScanType.Source
        elif scan_type in {"processed", "proc"}:
            self.type = ScanType.Proc
        else:
            raise ValueError(f"Unsupported scan type: {scan_type!r}")
        self.username = hdf5_string_reader(metaData["User_name"])
        self.projectDescription = hdf5_string_reader(metaData["Comment"])
        acqMetaData: h5py.Dataset = f["acqMetaData"]
        self.match_acquisition_mode(acqMetaData)
        return acqMetaData

    def match_acquisition_mode(self, acqMetaData: h5py.Dataset) -> None:
        """
        HDF5 helper function to correctly set the scan's acquisition mode

        Parameters
        ----------

        **acqMetaData**: h5py.Dataset
            The acquisition dataset

        Returns
        -------

        None
        """
        _acquisitionMode = hdf5_string_reader(acqMetaData["acquisitionMode"])
        match _acquisitionMode:
            case "2Dscan":
                self.acquisitionMode = AcquisitionMode.fUS2D
                self.probe.probeType = Probe.ProbeType.Linear
            case "3Dscan":
                self.acquisitionMode = AcquisitionMode.Angio3D
                if acqMetaData["imgDim"]["npose"][()] == 4:
                    self.probe.probeType = Probe.ProbeType.MultiArray
                else:
                    self.probe.probeType = Probe.ProbeType.Linear
            case "4Dscan":
                self.acquisitionMode = AcquisitionMode.fUS3D
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
                self.acquisitionMode = AcquisitionMode.fUS3DCustom
                self.probe.probeType = Probe.ProbeType.Linear
            case "4DscanRCA":
                self.acquisitionMode = AcquisitionMode.fUS3D
                self.probe.probeType = Probe.ProbeType.RCA
            case "3DscanRCA":
                self.acquisitionMode = AcquisitionMode.Angio3D
                self.probe.probeType = Probe.ProbeType.RCA
            case _:
                raise ValueError(f"Unsupported acquisition mode: {_acquisitionMode!r}")

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
        dzIcoBright = np.trunc(1e8 * 1540 * 1e-6 / 12.5)
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
        self.planeWaveAngles = np.arange(-10, 12, 2, dtype=float).tolist()
        if self.probe.name == "IcoPrime 4D MultiArray":
            self.planeWaveAngles = np.linspace(-12, 12, 8).tolist()
        self.transmitVoltage = 25
        self.pulseRepetitionFrequency = len(self.planeWaveAngles) * 500
        self.isMultiplane = False
        self.delayAfterTrigger = 0
        self.sequenceName = "default sequence"

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
        self.fill_ico_scan_version(
            hdf5_string_reader(f["scanMetaData"]["Neuroscan_version"])
        )

    def fill_ico_scan_version(self, neuroscan: str) -> None:
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
        neuroscan = neuroscan.strip()
        if neuroscan.startswith("Conexus Software version V"):
            version_text = neuroscan.removeprefix("Conexus Software version V")
        elif neuroscan.startswith("IcoScan version"):
            version_text = neuroscan.removeprefix("IcoScan version").strip()
        else:
            self.icoScanVersion = None
            return
        match = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?", version_text)
        if match is None:
            self.icoScanVersion = None
            return
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3) or 0)
        self.icoScanVersion = IcoScanVersion(major, minor, patch)

    def can_be_consolidated(self, hdf5_data: h5py.Dataset) -> bool:
        """
        Check whether the HDF5 data can use the regular consolidation path.

        Parameters
        ----------

        **hdf5_data**: h5py.Dataset
            The HDF5 root dataset

        Returns
        -------
        bool
            Returns True if the scan can be consolidated, False otherwise.
        """
        data_shape = hdf5_data["Data"].shape
        if (
            self.probe.probeType == Probe.ProbeType.RCA
            or self.acquisitionMode == AcquisitionMode.fUS3DCustom
            or (
                len(data_shape) > 4
                and data_shape[1] == 4
                and data_shape[4] == 1
                and self.acquisitionMode == AcquisitionMode.fUS3D
            )
        ):
            return False
        return True

    def _load_nonconsolidated_data(self, hdf5_data: h5py.Dataset) -> None:
        """Load HDF5 layouts that do not use regular consolidation."""
        data_shape = hdf5_data["Data"].shape
        if self.probe.probeType == Probe.ProbeType.RCA:
            data = hdf5_data["Data"][:].T
            time = hdf5_data["acqMetaData"]["timeOriginal"][:]
            self.measuredTimes = np.tile(time, (data.shape[1], 1)).tolist()
            self.probe.probeType = Probe.ProbeType.RCA
            self.voxels = data
        elif self.acquisitionMode == AcquisitionMode.fUS3DCustom:
            data = hdf5_data["Data"][:].T
            data = np.transpose(data, axes=(0, 1, 2, 5, 4, 3))
            blockRepeat: int = int(
                hdf5_data["acqMetaData"]["imgDim"]["nscanRepeat"][()][0][0]
            )
            nPose: int = int(hdf5_data["acqMetaData"]["imgDim"]["npose"][()][0][0])
            time = hdf5_data["acqMetaData"]["time"][:]
            self.measuredTimes = np.reshape(time, (nPose * blockRepeat)).tolist()
            self.probe.probeType = Probe.ProbeType.Linear
            self.voxels = data
        elif (
            len(data_shape) > 4
            and data_shape[1] == 4
            and data_shape[4] == 1
            and self.acquisitionMode == AcquisitionMode.fUS3D
        ):
            data = hdf5_data["Data"][:].T
            data = np.transpose(data, axes=(0, 3, 2, 5, 1, 6, 4))
            self.nPose = 4
            self.sizeY = 1
            time_original = np.asarray(hdf5_data["acqMetaData"]["timeOriginal"][:])
            self.measuredTimes = np.tile(time_original, (1, self.nPose)).tolist()
            self.probe.probeType = Probe.ProbeType.MultiArray
            self.voxels = data

    def load_scan_binary(self, filepath: str | os.PathLike[str]) -> None:
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
            dO, timeArraySize = self._load_binary_header(f)
            self._load_binary_timing_and_transforms(f, timeArraySize)
            f.seek(4, 1)
            acquisition_mode = _read_struct(f, "<L")
            self.acquisitionMode = {
                0: AcquisitionMode.fUS2D,
                1: AcquisitionMode.Angio3D,
                2: AcquisitionMode.fUS3D,
                3: AcquisitionMode.fUS3DCustom,
                4: AcquisitionMode.fUS3D,
                5: AcquisitionMode.Angio3D,
            }[acquisition_mode]
            f.seek(4, 1)
            self.probe = Probe()
            self.probe.load_binary(f)
            depthNear = _read_struct(f, "<d")
            depthFar = _read_struct(f, "<d")
            self.depth = Depth()
            self.depth.depthNear = depthNear
            self.depth.depthFar = depthFar
            self.ultrafastTransmitFrequency = _read_struct(f, "<d")
            self.pulseRepetitionFrequency = _read_struct(f, "<d")
            self.ultrafastSamplingFrequency = _read_struct(f, "<d")
            f.seek(8, 1)
            nPlaneWavesAngles = _read_struct(f, "<L")
            for _ in range(nPlaneWavesAngles):
                self.planeWaveAngles.append(_read_struct(f, "<d"))
            tempVal: int = _read_struct(f, "<L")
            f.seek(tempVal * 24 + 8, 1)
            self.transmitVoltage = _read_struct(f, "<d")
            f.seek(4, 1)
            self.delayAfterTrigger = _read_struct(f, "<d")
            tempVal = _read_struct(f, "<L")
            f.seek(tempVal * 8, 1)
            self.isMultiplane = _read_struct(f, "<?")
            f.seek(1, 1)
            self.integrationWindowDuration = _read_struct(f, "<d")
            self.sequenceName = read_string_binary(f, "<L", 4)
            self.projectTag = read_string_binary(f, "<L", 4)
            self.projectDescription = read_string_binary(f, "<L", 4)
            self.subjectTag = read_string_binary(f, "<L", 4)
            self.sessionTag = read_string_binary(f, "<L", 4)
            self.species = read_string_binary(f, "<L", 4)
            self.gender = GenderType(_read_struct(f, "<L"))
            self.transferDate = datetime.fromtimestamp(_read_struct(f, "<q"), pytz.utc)
            self.ageAtTransfer = _read_struct(f, "<Q")
            self.subjectDescription = read_string_binary(f, "<L", 4)
            self.weightUnit = WeightUnitType(_read_struct(f, "<L"))
            self.weight = _read_struct(f, "<f")
            self.treatment = read_string_binary(f, "<L", 4)
            self.scanTag = read_string_binary(f, "<L", 4)
            self.studyType = read_string_binary(f, "<L", 4)
            self.taskName = read_string_binary(f, "<L", 4)
            self.taskDescription = read_string_binary(f, "<L", 4)
            self.username = read_string_binary(f, "<L", 4)
            for _ in range(2):
                tempVal = _read_struct(f, "<L")
                f.seek(tempVal, 1)
            self.acquisitionDate = datetime.fromtimestamp(
                _read_struct(f, "<q"), pytz.utc
            )
            self.type = ScanType(_read_struct(f, "<L"))
            toggleTimes: int = _read_struct(f, "<L")
            for _ in range(toggleTimes):
                self.stimulationToggleTimes.append(_read_struct(f, "<f"))
            icoScanMajor = _read_struct(f, "<L")
            icoScanMinor = _read_struct(f, "<L")
            icoScanPatch = _read_struct(f, "<L")
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
            if dataSize < 0:
                raise ValueError("scan voxel count must be non-negative")
            remaining_bytes = os.fstat(f.fileno()).st_size - f.tell()
            if remaining_bytes < dataSize * np.dtype("<f8").itemsize:
                raise OSError("binary scan voxel data is truncated")
            self.voxels = np.fromfile(f, dtype="<f8", count=dataSize)
            if self.voxels.size != dataSize:
                raise OSError("binary scan voxel data is truncated")
            self.voxels = self.voxels.reshape(
                (
                    self.sizeX,
                    self.sizeY,
                    self.sizeZ,
                    self.nTime,
                    self.nPose,
                    self.dim6.count,
                ),
                order="F",
            )

    def _load_binary_header(self, f: BufferedReader) -> tuple[int, int]:
        """Load binary dimensions and return the data offset and timing size."""
        f.seek(32)
        dO: int = _read_struct(f, "<Q")
        f.seek(92)
        self.sizeX = _read_struct(f, "<Q")
        self.sizeY = _read_struct(f, "<Q")
        self.sizeZ = _read_struct(f, "<Q")
        self.nTime = _read_struct(f, "<Q")
        self.nPose = _read_struct(f, "<Q")
        if min(self.sizeX, self.sizeY, self.sizeZ, self.nTime, self.nPose) <= 0:
            raise ValueError("scan dimensions must be positive")
        self.dim6 = Dim6()
        self.dim6.load_binary(f)
        self.voxDim = VoxDim()
        self.voxDim.load_binary(f)
        timeArraySize: int = self.sizeY * self.nTime * self.nPose
        return dO, timeArraySize

    def _load_binary_timing_and_transforms(
        self, f: BufferedReader, timeArraySize: int
    ) -> None:
        """Load timing arrays and probe transforms from a binary scan."""
        if timeArraySize > os.fstat(f.fileno()).st_size // 8:
            raise OSError("binary scan timing data is truncated")
        self.measuredTimes = [_read_struct(f, "<d") for _ in range(timeArraySize)]
        self.theoreticalTimeIndices = [
            _read_struct(f, "<L") for _ in range(timeArraySize)
        ]
        self.probeToLabsTranslations = np.ndarray(shape=(self.nPose, 3))
        self.probeToLabsRotations = np.ndarray(shape=(self.nPose, 3))
        for i in range(self.nPose):
            self.probeToLabsTranslations[i] = [_read_struct(f, "<d") for _ in range(3)]
        for i in range(self.nPose):
            self.probeToLabsRotations[i] = [_read_struct(f, "<d") for _ in range(3)]

    def get_voxel_to_probe(self) -> np.ndarray:
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
        shift_voxel: np.ndarray = translation_matrix(-1, -1, -1)
        center_probe: np.ndarray = translation_matrix(
            (float)(-((self.sizeX - 1) / 2)), (float)(-((self.sizeY - 1) / 2)), 0
        )
        scale_to_metric: np.ndarray = scale_matrix(
            self.voxDim.dx, self.voxDim.dy, -self.voxDim.dz
        )
        move_probe_up: np.ndarray = translation_matrix(
            0, 0, 0.001 * -self.depth.depthNear
        )
        return move_probe_up @ scale_to_metric @ center_probe @ shift_voxel

    def get_probe_to_lab(self) -> list[np.ndarray]:
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
        for i in range(len(self.probeToLabsRotations)):
            rot = (
                self.probeToLabsRotations[i][0],
                self.probeToLabsRotations[i][1],
                self.probeToLabsRotations[i][2],
            )
            Rm = rotation_xyz(rot)
            Rm.T[3][0] = self.probeToLabsTranslations[i][0]
            Rm.T[3][1] = self.probeToLabsTranslations[i][1]
            Rm.T[3][2] = self.probeToLabsTranslations[i][2]
            rep.append(Rm)
        return rep

    def __str__(self) -> str:
        rep = (
            f"sizeX: {self.sizeX}\nsizeY: {self.sizeY}\nsizeZ: {self.sizeZ}\nnTime: {self.nTime}\nnPose: {self.nPose}"
            f"\ndim6: {self.dim6}\nvoxDim: {self.voxDim}\nmeasuredTimes: {len(self.measuredTimes)} ({self.sizeY} * {self.nTime} * {self.nPose}) (sizeY * nTime * nPose)\n"
            f"theoreticalTimeIndices: {len(self.theoreticalTimeIndices)} ({self.sizeY} * {self.nTime} * {self.nPose}) (sizeY * nTime * nPose)\n"
            f"probeToLabsTranslation: {self.probeToLabsTranslations}\nprobeToLabsRotations: {self.probeToLabsRotations}\n"
            f"acquisitionMode: {self.acquisitionMode.name}\nprobe: {self.probe}\ndepth: {self.depth}\n"
            f"ultrafastTransmitFrequency: {self.ultrafastTransmitFrequency}\npulseRepetitionFrequency: {self.pulseRepetitionFrequency}\n"
            f"ultrafastSamplingFrequency: {self.ultrafastSamplingFrequency}\nplaneWavesAngles: {len(self.planeWaveAngles)}\n"
        )
        for i in range(len(self.planeWaveAngles)):
            rep += f"\t{i}: {self.planeWaveAngles[i]}\n"
        rep += (
            f"transmitVoltage: {self.transmitVoltage}\ndelayAfterTrigger: {self.delayAfterTrigger}\nisMultiplane: {self.isMultiplane}\n"
            f"integrationWindowDuration: {self.integrationWindowDuration}\nsequenceName: {self.sequenceName}\nprojectTag: {self.projectTag}\n"
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
        self.dx = float(voxDimData["dx"][0][0])
        if dy is None:
            self.dy = float(voxDimData["dy"][0][0])
        else:
            self.dy = dy
        self.dz = float(voxDimData["dz"][0][0])
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
        self.dx = _read_struct(f, "<d")
        self.dy = _read_struct(f, "<d")
        self.dz = _read_struct(f, "<d")
        self.dt = _read_struct(f, "<d")
        self.dr = _read_struct(f, "<d")
        self.dtheta = _read_struct(f, "<d")

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
        ClutterFiltering = 0
        EnhancedDoppler = 1
        VelocityBandFiltering = 2
        BrainMaskedDoppler = 3

    class ClutterFiltering:
        class clutterFilterType(IntEnum):
            StaticSVD = 0
            DynamicSVD = 1
            Butterworth = 2

        def __init__(self) -> None:
            self.clutterFilter: Dim6.ClutterFiltering.clutterFilterType
            self.clutterFilterWindowDuration: float
            self.clutterFilterCutoffLow: float
            self.clutterFilterCutoffHigh: float

        def load_binary(self, f: BufferedReader) -> object:
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
            self.clutterFilter = self.clutterFilterType(_read_struct(f, "<L"))
            self.clutterFilterWindowDuration = _read_struct(f, "<d")
            if (
                self.clutterFilter == self.clutterFilterType.StaticSVD
                or self.clutterFilter == self.clutterFilterType.DynamicSVD
            ):
                self.clutterFilterCutoffLow = _read_struct(f, "<L")
                self.clutterFilterCutoffHigh = _read_struct(f, "<L")
            else:
                self.clutterFilterCutoffLow = _read_struct(f, "<f")
                self.clutterFilterCutoffHigh = _read_struct(f, "<f")
            return self

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

        def load_binary(self, f: BufferedReader) -> object:
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
            self.velocityMin = _read_struct(f, "<f")
            self.velocityMax = _read_struct(f, "<f")
            f.seek(12, 1)
            return self

        def __str__(self) -> str:
            return f"\t\tVelocity Min: {self.velocityMin}\n\t\tVelocity Max: {self.velocityMax}\n"

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
        self.count = _read_struct(f, "<Q")
        if self.count > (os.fstat(f.fileno()).st_size - f.tell()) // 4:
            raise OSError("binary scan dim6 data is truncated")
        dim6intents: list[int] = []
        for _ in range(self.count):
            dim6intents.append(_read_struct(f, "<L"))
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
    fUS2D = 0
    Angio3D = 1
    fUS3D = 2
    fUS3DCustom = 3


class Probe:
    class ProbeType(IntEnum):
        Linear = 0
        MultiArray = 1
        RCA = 2
        Phased = 3
        Matrix = 4

    def __init__(self) -> None:
        self.name: str
        self.probeType: Probe.ProbeType
        self.probeCentralFrequency: float | None
        self.probePitch: float | None
        self.probeElevationAperture: float | None
        self.probeRadiusOfCurvature: float | None
        self.probeNumberOfElements: int | None
        self.probeModel: str | None

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
        self.probeCentralFrequency = None
        self.probePitch = None
        self.probeElevationAperture = None
        self.probeNumberOfElements = None
        self.probeModel = None
        if self.name in {"IcoPrime", "unknown", "IcoPrime 4D MultiArray"}:
            self.probeCentralFrequency = 15.625
            self.probePitch = 0.11
            self.probeElevationAperture = 1.5
            self.probeNumberOfElements = (
                256 if self.name == "IcoPrime 4D MultiArray" else 128
            )
            self.probeModel = (
                "2390" if self.name == "IcoPrime 4D MultiArray" else "2392"
            )
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
        self.probeType = self.ProbeType(_read_struct(f, "<L"))
        self.probeCentralFrequency = _read_struct(f, "<d")
        self.probePitch = _read_struct(f, "<d")
        self.probeElevationAperture = _read_struct(f, "<d")
        f.seek(8, 1)
        self.probeRadiusOfCurvature = _read_struct(f, "<d")
        self.probeNumberOfElements = _read_struct(f, "<H")
        self.probeModel = read_string_binary(f, "<H", 2)
        self.name = read_string_binary(f, "<H", 2)

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
