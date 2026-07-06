import numpy as np
import h5py
from ..utils.utils import decryptData
from .Scan import Depth, VoxDim

class Raw:
    class MetaData:
        def __init__(self, fileheader):
            h5 = h5py.File(fileheader, "r")
            self.transmitFrequency = float(decryptData(h5["F1"], 1)[0])
            self.prf = float(decryptData(h5["F2"], 2)[0])
            self.speedOfSound = float(decryptData(h5["F3"], 3)[0])
            self.frameRate = float(decryptData(h5["F4"], 4)[0])
            self.receiveAperture = decryptData(h5["F5"], 5)
            self.flatAngles = decryptData(h5["F7"], 7)
            self.blockDim = decryptData(h5["F9"], 9)
            self.compound = bool(decryptData(h5["F10"], 10)[0])
            self.numberOfBlock = int(decryptData(h5["F11"], 11)[0])
            self.acquisitionMode = h5["F13"][()][0][0].decode("utf-8")
            depthData = decryptData(h5["F6"], 6)
            voxDimData = decryptData(h5["F8"], 8)
            self.depth = Depth(depthData[0], depthData[1])
            self.voxDim = VoxDim(voxDimData[0], voxDimData[1], voxDimData[2])
            self.isCrypted = bool(decryptData(h5["F12"], 12)[0])

    def __init__(self, filepath, file_header, blockStart=1, blockEnd=1):
        self.metadata = Raw.MetaData(file_header)
        nCompound = int(self.metadata.blockDim[3][0])
        nFramesPerBlock = int(self.metadata.blockDim[4][0])
        sizeX = int(self.metadata.blockDim[0][0])
        sizeY = int(self.metadata.blockDim[1][0])
        sizeZ = int(self.metadata.blockDim[2][0])
        with open(filepath, "rb") as f:
            if self.metadata.isCrypted:
                f.seek(117)
            nBlockToSkip = blockStart - 1
            if nBlockToSkip > 0:
                sizeToSkip = (
                    nBlockToSkip * nFramesPerBlock * nCompound * sizeX * sizeZ * 2 * 4
                )
                f.seek(sizeToSkip, 1)
            nBlockToRead = 1
            if blockEnd > blockStart:
                blockEnd = min(blockEnd, self.metadata.numberOfBlock)
                nBlockToRead = blockEnd - nBlockToSkip

            n_elements = int(
                2 * sizeX * sizeY * sizeZ * nCompound * nFramesPerBlock * nBlockToRead
            )
            iQt = np.fromfile(f, dtype="<f4", count=n_elements)
        iQt = iQt.reshape(
            (2, sizeZ, sizeY, sizeX, nCompound, nFramesPerBlock, nBlockToRead), order="F"
        )
        iQblock = iQt[0, ...] + 1j * iQt[1, ...]
        iQblock = np.squeeze(iQblock)

        if nCompound > 1:
            # IQblock = mycompoundMethod(IQblock)
            pass
        self.data = iQblock
