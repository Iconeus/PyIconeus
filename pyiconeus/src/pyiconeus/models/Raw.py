import numpy as np
import h5py
from ..utils.utils import decryptData
from .Scan import Depth, VoxDim


class Raw:
    class MetaData:
        def __init__(self, fileheader):
            with h5py.File(fileheader, "r") as h5:
                self.transmitFrequency: float = float(decryptData(h5["F1"], 1)[0])
                self.prf: float = float(decryptData(h5["F2"], 2)[0])
                self.speedOfSound: float = float(decryptData(h5["F3"], 3)[0])
                self.frameRate: float = float(decryptData(h5["F4"], 4)[0])
                self.receiveAperture: np.ndarray = decryptData(h5["F5"], 5)
                self.flatAngles: np.ndarray = decryptData(h5["F7"], 7)
                self.blockDim: np.ndarray = decryptData(h5["F9"], 9)
                self.compound: bool = bool(decryptData(h5["F10"], 10)[0])
                self.numberOfBlock: int = int(decryptData(h5["F11"], 11)[0])
                self.acquisitionMode: str = h5["F13"][()][0][0].decode("utf-8")
                depthData: np.ndarray = decryptData(h5["F6"], 6)
                voxDimData: np.ndarray = decryptData(h5["F8"], 8)
                self.depth = Depth()
                self.depth.depthNear = depthData[0]
                self.depth.depthFar = depthData[1]
                self.voxDim = VoxDim(voxDimData[0], voxDimData[1], voxDimData[2])
                self.isCrypted: bool = bool(decryptData(h5["F12"], 12)[0])

    def __init__(self, filepath, file_header, blockStart=1, blockEnd=1):
        self.metadata = Raw.MetaData(file_header)
        nCompound: int = int(self.metadata.blockDim[3][0])
        nFramesPerBlock: int = int(self.metadata.blockDim[4][0])
        sizeX: int = int(self.metadata.blockDim[0][0])
        sizeY: int = int(self.metadata.blockDim[1][0])
        sizeZ: int = int(self.metadata.blockDim[2][0])
        with open(filepath, "rb") as f:
            if self.metadata.isCrypted:
                f.seek(117)
            nBlockToSkip: int = blockStart - 1
            if nBlockToSkip > 0:
                sizeToSkip: int = (
                    nBlockToSkip * nFramesPerBlock * nCompound * sizeX * sizeZ * 2 * 4
                )
                f.seek(sizeToSkip, 1)
            nBlockToRead = 1
            if blockEnd > blockStart:
                blockEnd: int = min(blockEnd, self.metadata.numberOfBlock)
                nBlockToRead = blockEnd - nBlockToSkip

            n_elements = int(
                2 * sizeX * sizeY * sizeZ * nCompound * nFramesPerBlock * nBlockToRead
            )
            iQt: np.ndarray = np.fromfile(f, dtype="<f4", count=n_elements)
        iQt: np.ndarray = iQt.reshape(
            (2, sizeZ, sizeY, sizeX, nCompound, nFramesPerBlock, nBlockToRead),
            order="F",
        )
        iQblock: np.ndarray = iQt[0, ...] + 1j * iQt[1, ...]
        iQblock = np.squeeze(iQblock)

        if nCompound > 1:
            # IQblock = mycompoundMethod(IQblock)
            pass
        self.data: np.ndarray = iQblock
