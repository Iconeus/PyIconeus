The ``.raw`` format
======================

This page is dedicated to the IQ format ``.raw`` and its associated ``.hraw``
metadata header. The two files are required together.

.. contents:: On this page
   :local:
   :depth: 2

Raw
------

Attributes
+++++++++++++

metadata : MetaData
    metadata of the raw file (mandatory)

data : np.ndarray
    NumPy array containing the complex IQ data after beamforming. The leading
    dimensions are ordered as ``(sizeZ, sizeY, sizeX, compound, frames, blocks)``
    before singleton dimensions are removed by ``numpy.squeeze``.

MetaData
---------

Attributes
+++++++++++

acquisitionMode: str
    Description of the type of acquisition (ex: 2Dscan, 3Dscan, ...)

transmitFrequency : float
    The transmit frequency of the acquisition, in MHz

prf : float
    The pulse repetition frequency, Hz

speedOfSound : float
    The speed of sound, in meter per second

frameRate : float
    Frame rate of the acquisition, in Hz

receiveAperture : np.ndarray
    Receive aperture, first and last elements of the aperture

depth : Scan.Depth
    Near and Far depth, in millimeter

flatAngles : np.ndarray
    Angles of the probe during the acquisition, in degrees

voxDim : Scan.VoxDim
    Voxel dimension x, y and z, in meters

blockDim : np.ndarray
    Block dimension x, y, z, angle, frame 
    
compound : bool
    True if the images are compounded, False otherwise

numberOfBlock : int
    Number of blocks

isLegacyFormat : bool
    True if the file uses the legacy raw data block layout from early
    ``.raw`` acquisitions, False otherwise

Block selection
---------------

``open_path`` accepts the optional ``blockStart`` and ``blockEnd`` arguments.
They are one-based and inclusive, and default to block 1. If ``blockEnd`` is
greater than ``numberOfBlock``, it is clamped to the available number of
blocks and a ``RuntimeWarning`` is emitted. ``blockEnd`` smaller than
``blockStart`` raises ``RuntimeError``.
