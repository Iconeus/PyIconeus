The ``.raw`` format
======================

This page is dedicated to the IQ format '.raw', and its associated '.hraw' format

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
	numpy array containing the raw data after th beamforming

MetaData
---------

Attributes
+++++++++++

transmitFraquency : float
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

isCrypted : bool
    Is the IQ crypted or not

acquisitionMode : str
	Type of acquisition
