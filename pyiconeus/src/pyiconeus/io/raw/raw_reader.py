from ...models.Raw import Raw
from ...models.Scan import Depth, VoxDim
import numpy as np
import h5py

def decryptData(value, n: int):
    if (value.shape[0] == 1):
        nbrc = np.asarray(value, dtype=float)[0]
    else:
        nbrc = np.asarray(value, dtype=float)
    nbr = nbrc.copy()
    if nbrc.ndim < 3:
        nbr = (nbrc - 72) / (1005 * n)
    return nbr

def read_hraw_binary(fileheader):
    return

def read_hraw_hdf5(fileheader):
    metadata: Raw.MetaData = Raw.MetaData()
    h5 = h5py.File(fileheader, 'r')
    metadata.transmitFrequency = float(decryptData(h5['F1'], 1)[0])
    metadata.prf = float(decryptData(h5['F2'], 2)[0])
    metadata.speedOfSound = float(decryptData(h5['F3'], 3)[0])
    metadata.frameRate = float(decryptData(h5['F4'], 4)[0])
    metadata.receiveAperture = decryptData(h5['F5'], 5)
    metadata.flatAngles = decryptData(h5['F7'], 7)
    metadata.blockDim = decryptData(h5['F9'], 9)
    metadata.compound = bool(decryptData(h5['F10'], 10)[0])
    metadata.numberOfBlock = int(decryptData(h5['F11'], 11)[0])
    metadata.acquisitionMode = h5['F13'][()][0][0].decode('utf-8')
    depthData = decryptData(h5['F6'], 6)
    voxDimData = decryptData(h5['F8'], 8)
    metadata.depth = Depth(depthData[0], depthData[1])
    metadata.voxDim = VoxDim(voxDimData[0],voxDimData[1],voxDimData[2])
    return (metadata, decryptData(h5['F12'], 12))


def raw_reader_binary(filepath, fileheader):
    return

def raw_reader_hdf5(filepath, fileheader, blockStart=0, blockEnd=1):
    (metaData, seek) = read_hraw_hdf5(fileheader)
    return metaData
