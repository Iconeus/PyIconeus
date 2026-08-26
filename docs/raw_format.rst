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

transmitFrequency : float
    The transmit frequency of the acquisition

prf : float
    The pulse repetition frequency

speedOfSound : float
    The speed of sound

frameRate : float
    Frame rate of the acquisition

receiveAperture : np.ndarray
    Receive Aperture

depth : Scan.Depth
    Near and Far depth

flatAngles : np.ndarray
    Angles of the probe during the acquisition

voxDim : Scan.VoxDim
    VoxDim data

blockDim : np.ndarray
    BlockDim data

compound : bool
    True if the images are compounded, False otherwise

numberOfBlock : int
    Number of blocks

isLegacyFormat : bool
    True if the file uses the legacy metadata encoding and binary layout
    from early ``.raw`` files, False otherwise

Block selection
---------------

``open_path`` accepts the optional ``blockStart`` and ``blockEnd`` arguments.
They are one-based and inclusive, and default to block 1. If ``blockEnd`` is
greater than ``numberOfBlock``, it is clamped to the available number of
blocks and a ``RuntimeWarning`` is emitted. ``blockEnd`` smaller than
``blockStart`` raises ``RuntimeError``.

acquisitionMode : str
	Type of acquisition
