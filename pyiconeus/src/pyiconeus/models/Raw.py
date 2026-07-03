import numpy as np
from .Scan import Depth, VoxDim

class Raw:
    class MetaData:
        def __init__(self):
            self.transmitFrequency: float
            self.prf: float
            self.speedOfSound: float
            self.frameRate: float
            self.receiveAperture: np.ndarray
            self.depth: Depth
            self.flatAngles: np.ndarray
            self.voxDim: VoxDim
            self.blockDim: np.ndarray
            self.compound: bool
            self.numberOfBlock: int
            self.acquisitionMode: str

    def __init__(self):
        self.data: np.ndarray
        self.metadata: Raw.MetaData
