The ``.scan`` format
======================

This page is dedicated to the Scan format '.scan' and its different helpers classes.

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
    Frequency of the transmit, in Mhz

pulseRepetitionFrequency : float
    Frequency of pulse repetition, in Mhz

ultrafastSamplingFrequency : float
    Frequency of the ultra fast sampling, in Mhz

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

theoricalTimeIndices : list[int]
    Indices of the measuredTimes list

probeToLabsTranslations : :class:`~pyiconeus.models.Scan.ProbeToLabElements`
    Mean translation per probe rotation, see the :ref:`probetolab-section` section below

probeToLabsRotations : :class:`~pyiconeus.models.Scan.ProbeToLabElements`
    List of rotation of the probe

voxels : numpy.ndarray
    The actual data of the acquisition
    shape = (sizeX, sizeY, sizeZ, nTime, nPose, dim6)

Format & version
++++++++++++++++++

icoScanVersion : :class:`~pyiconeus.models.Scan.IcoScanVersion` | None
    Version of the icoScan software that took the acquisition, see the :ref:`icoscanversion-section` section below.
    ``None`` for old scans.

bps : :class:`~pyiconeus.models.Bps.Bps`
    Placeholder for a BPS element. Its the Brain Positioning System for a specific scan

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

probeCentralFrequency : float
    in Mhz

probePitch : float
    in millimeters

probeElevationAperture : float
    in millimeters

probeRadiusOfCurvature : float
    in millimeters

probeNumberOfElements : float
    One of `64`, `128`, `160`, `192`, `256`, `1024`

probeModel : str
    Serial number of the probe

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
``BrainMaskedDoppler``. *(TODO - describe each value.)*

ClutterFiltering
++++++++++++++++++

clutterFilter : clutterFilterType (``StaticSVD`` | ``DynamicSVD`` | ``Butterworth``)
    *(TODO - describe each filter type.)*

clutterFilterWindowDuration : float
    *(TODO - specify the unit.)*

clutterFilterCutoffLow, clutterFilterCutoffHigh : float
    *(TODO - specify the unit; note that the type differs depending on the
    filter: int for SVD-based filters, float for Butterworth.)*

VelocityBandwidthFiltering
++++++++++++++++++++++++++++

velocityMin, velocityMax : float
    *(TODO - specify the unit, e.g. mm/s.)*

.. _probetolab-section:

ProbeToLabElements
--------------------

matricesCount : int
    Number of matrices

matricesList : list[ProbeToLabMatrices]
    List of matrices

ProbeToLabMatrices
+++++++++++++++++++

x, y, z : float
    Vector of translation or rotation

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
Source scans are coming directly out of icoScan.
Proc scans are processed scans.

AcquisitionMode
++++++++++++++++

``_2DScan``, ``_3DScan``, ``_4DScan``, ``_4DScanCustom``, ``_4DscanRCA``,
``_3DscanRCA``
