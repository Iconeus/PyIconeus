The ``.scan`` format
======================

This page is dedicated to the ``.scan`` format and its helper classes. PyIconeus
supports both legacy HDF5 scans and binary scans.

.. contents:: On this page
   :local:
   :depth: 2

Scan
-----

Identification & scan metadata
++++++++++++++++++++++++++++++++++

The following attributes of this section are user defined, unless stated otherwise

projectTag : str
    Tag of the project

projectDescription : str
    Description of the project

scanTag : str
    Tag of the scan

subjectTag : str
    Tag of the subject

sessionTag : str
    Tag of the session

studyType : str
    Type of study

taskName : str
    Name of the task

taskDescription : str
    Description of the task

sequenceName : str
    Name of the sequence

username : str
    Username

treatment : str
    Type of treatment

Subject metadata
++++++++++++++++++

species : str
    Species of the subject

gender : :class:`~pyiconeus.models.Scan.GenderType`
    Gender of the subject

transferDate : datetime.datetime
    Date of the transfer

ageAtTransfer : int
    Age at the transfer

subjectDescription : str
    Description of the subject

weight : float
    Weight of the subject, in **weightUnit**

Acquisition parameters
++++++++++++++++++++++++

acquisitionMode : :class:`~pyiconeus.models.Scan.AcquisitionMode`
    Description of the type of acquisition (ex: 3DScan, 4DScan, ...)

acquisitionDate : datetime.datetime
    Date of the acquisition

type : :class:`~pyiconeus.models.Scan.ScanType`
    'Source' or 'Proc', if the scan has been modified

probe : :class:`~pyiconeus.models.Scan.Probe`
    Description about the probe used for the Acquisition, see the :ref:`probe-section` section below

depth : :class:`~pyiconeus.models.Scan.Depth`
    Depth far and near of the acquisition, see the :ref:`depth-section` *section below*

ultrafastTransmitFrequency : float
    Frequency of the transmit, in MHz

pulseRepetitionFrequency : float
    Frequency of pulse repetition, in kHz

ultrafastSamplingFrequency : float
    Frequency of the ultra fast sampling, in MHz

planeWaveAngles : list[float]
    List of the plane waves angles

transmitVoltage : float
    Voltage of the transmit

delayAfterTrigger : float
    Delay after each trigger

isMultiplane : bool
    True if the acquisition is multiplane

integrationWindowDuration : float
    Time of the window duration

stimulationToggleTimes : list[float]
    List of the times the stimulation was toggled

Geometry, timing & data
+++++++++++++++++++++++++

sizeX, sizeY, sizeZ : int
    Dimension of the acquisition:
        - sizeX: Width size in number of voxels
        - sizeY: Height size in number of voxels
        - sizeZ: Depth in number of voxels

nTime : int
    Number of time a full block has been acquired (block = [sizeX, sizeY, sizeZ])

nPose : int
    Number of probe position, set to 1 after consolidation of the acquisition

voxDim : :class:`~pyiconeus.models.Scan.VoxDim`
    voxel size in meters, see the :ref:`voxdim-section` section below.

dim6 : :class:`~pyiconeus.models.Scan.Dim6`
    Description about additional filters, see the :ref:`dim6-section` section below.

measuredTimes : list[float]
    List containing the times of every acquired block

theoreticalTimeIndices : list[int]
    Indices of the measuredTimes list

probeToLabsTranslations : numpy.ndarray
    Array of mean translations, with shape ``(nPose, 3)``.

probeToLabsRotations : numpy.ndarray
    Array of rotations in radians, with shape ``(nPose, 3)``.

The :meth:`~pyiconeus.models.Scan.Scan.get_ProbeToLab` method combines these
values into one 4x4 affine matrix per pose. The
:meth:`~pyiconeus.models.Scan.Scan.get_VoxelToProbe` method returns the 4x4
voxel-to-probe affine matrix.

voxels : numpy.ndarray
    The actual data of the acquisition. Binary scans use the shape
    ``(sizeX, sizeY, sizeZ, nTime, nPose, dim6)``. Legacy HDF5 scans may be
    consolidated while loading; inspect ``voxels.shape`` for the exact result.

Format & version
++++++++++++++++++

icoScanVersion : :class:`~pyiconeus.models.Scan.IcoScanVersion` | None
    Version of the icoScan software that took the acquisition, see the :ref:`icoscanversion-section` section below.
    ``None`` for old scans.

bps : :class:`~pyiconeus.models.Bps.Bps`
    Placeholder for a BPS element. It's the Brain Positioning System for a specific scan

.. _voxdim-section:

VoxDim
-------

dx, dy, dz : float
    Voxel size along each axis in meters

dt : float
    Time in seconds at the end of the acquisition of the first block of the first probe position including the pause. This is not necessarily volumetric dt

dr : float
    Voxel angle in radians

dtheta : float
    Voxel angle in radians

.. _probe-section:

Probe
------

name : str
    Name of the probe

probeType : :class:`Probe.ProbeType <pyiconeus.models.Scan.Probe.ProbeType>`
    One of ``Linear``, ``MultiArray``, ``RCA``, ``Phased``, ``Matrix``.

probeCentralFrequency : float or None
    Probe central frequency in MHz when available.

probePitch : float or None
    Probe pitch in millimeters when available.

probeElevationAperture : float or None
    Elevation aperture in millimeters when available.

probeRadiusOfCurvature : float
    in millimeters

probeNumberOfElements : int or None
    Number of probe elements when available.

probeModel : str or None
    Probe model or serial number when available.

.. _depth-section:

Depth
------

depthNear : float
    in millimeters

depthFar : float
    in millimeters

.. _dim6-section:

Dim6
-----

count : int
    Number of dim6 elements.

dim6element : set[tuple[Dim6Intent, object]]
    Set of all the Dim6Intents

Dim6Intent
+++++++++++

One of ``ClutterFiltering``, ``EnhancedDoppler``, ``VelocityBandFiltering``,
``BrainMaskedDoppler``. The corresponding intent-specific payload is exposed
through ``dim6element`` when it is implemented by the binary reader.

ClutterFiltering
++++++++++++++++++

clutterFilter : clutterFilterType (``StaticSVD`` | ``DynamicSVD`` | ``Butterworth``)

clutterFilterWindowDuration : float
    Duration of the filter in seconds

clutterFilterCutoffLow, clutterFilterCutoffHigh : float

VelocityBandwidthFiltering
++++++++++++++++++++++++++++

velocityMin, velocityMax : float
    Minimum and maximum velocity values as stored in the file. The reader does
    not convert their unit.

.. _icoscanversion-section:

IcoScanVersion
----------------

major, minor, patch : int
    Version  identification numbers

Enumerations
-------------

GenderType
+++++++++++

``Undefined``, ``Male``, ``Female``, ``Other``

WeightUnitType
+++++++++++++++

``mg``, ``g``, ``kg``

ScanType
+++++++++

``Source``, ``Proc``
Proc scans are processed scans.

AcquisitionMode
++++++++++++++++

``_2DScan``, ``_3DScan``, ``_4DScan``, ``_4DScanCustom``, ``_4DscanRCA``,
``_3DscanRCA``
