import pyiconeus
from pyiconeus.utils.utils import decryptData
from pyiconeus.io.base import read_raw
from pyiconeus.models.Scan import Depth, VoxDim
import numpy as np


def test_read_raw():
    raw = read_raw(
        "./tests/data" + "/TestULM2D_v2.raw", "./tests/data" + "/TestULM2D_v2.hraw"
    )
    assert isinstance(raw, pyiconeus.Raw)


def test_raw_val():
    raw = read_raw(
        "./tests/data" + "/TestULM2D_v2.raw", "./tests/data" + "/TestULM2D_v2.hraw"
    )
    metadata: pyiconeus.Raw.MetaData = pyiconeus.Raw.MetaData("./tests/data" + "/TestULM2D_v2.hraw")
    metadata.transmitFrequency = float(decryptData(np.array([15775.125]), 1))
    metadata.prf = float(decryptData(np.array([22110072]), 2))
    metadata.speedOfSound = float(decryptData(np.array([4643172]), 3))
    metadata.frameRate = float(decryptData(np.array([4020072]), 4))
    metadata.receiveAperture = decryptData(np.array([5097, 643272]), 5)
    metadata.flatAngles = decryptData(
        np.array(
            [
                -70278,
                -56208,
                -42138,
                -28068,
                -13998,
                72,
                14142,
                28212,
                42282,
                56352,
                70422,
            ]
        ),
        7,
    )
    metadata.blockDim = decryptData(np.array([1157832, 9117, 823167, 9117, 3618072]), 9)
    metadata.compound = bool(decryptData(np.array([10122]), 10))
    metadata.numberOfBlock = int(decryptData(np.array([99567]), 11))
    metadata.acquisitionMode = "2Dscan"
    depthData = decryptData(np.array([6102, 60372]), 6)
    voxDimData = decryptData(np.array([956.4, 3288, 864.4223999999999]), 8)
    metadata.depth = Depth()
    metadata.depth.depthNear = depthData[0]
    metadata.depth.depthFar = depthData[1]
    metadata.voxDim = VoxDim(voxDimData[0], voxDimData[1], voxDimData[2])
    assert metadata.transmitFrequency == raw.metadata.transmitFrequency
    assert metadata.prf == raw.metadata.prf
    assert metadata.speedOfSound == raw.metadata.speedOfSound
    assert metadata.frameRate == raw.metadata.frameRate
    assert metadata.receiveAperture[0] == raw.metadata.receiveAperture[0]
    assert metadata.flatAngles[0] == raw.metadata.flatAngles[0]
    assert metadata.blockDim[0] == raw.metadata.blockDim[0]
    assert metadata.compound == raw.metadata.compound
    assert metadata.numberOfBlock == raw.metadata.numberOfBlock
    assert metadata.acquisitionMode == raw.metadata.acquisitionMode
    assert metadata.depth.depthFar == raw.metadata.depth.depthFar
    assert metadata.depth.depthNear == raw.metadata.depth.depthNear
    assert metadata.voxDim.dx == raw.metadata.voxDim.dx
    assert metadata.voxDim.dy == raw.metadata.voxDim.dy
    assert metadata.voxDim.dz == raw.metadata.voxDim.dz
