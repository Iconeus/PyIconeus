# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import h5py
import numpy as np
from pytest import mark

import pyiconeus
from pyiconeus import Raw
from pyiconeus.models.Scan import Depth, VoxDim
from pyiconeus.utils.utils import decrypt_data


def test_read_raw():
    raw = Raw("./tests/data" + "/2DScan_v2.raw", "./tests/data" + "/2DScan_v2.hraw")
    assert isinstance(raw, pyiconeus.Raw)


def test_raw_val():
    raw = Raw("./tests/data" + "/2DScan_v2.raw", "./tests/data" + "/2DScan_v2.hraw")
    metadata: pyiconeus.Raw.MetaData = pyiconeus.Raw.MetaData(
        "./tests/data" + "/2DScan_v2.hraw"
    )
    metadata.transmitFrequency = float(decrypt_data(np.array([15775.125]), 1))
    metadata.prf = float(decrypt_data(np.array([22110072]), 2))
    metadata.speedOfSound = float(decrypt_data(np.array([4643172]), 3))
    metadata.frameRate = float(decrypt_data(np.array([4020072]), 4))
    metadata.receiveAperture = decrypt_data(np.array([5097, 643272]), 5)
    metadata.flatAngles = decrypt_data(
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
    metadata.blockDim = decrypt_data(
        np.array([1157832, 9117, 823167, 9117, 3618072]), 9
    )
    metadata.compound = bool(decrypt_data(np.array([10122]), 10))
    metadata.numberOfBlock = int(decrypt_data(np.array([99567]), 11))
    metadata.acquisitionMode = "2Dscan"
    depthData = decrypt_data(np.array([6102, 60372]), 6)
    voxDimData = decrypt_data(np.array([956.4, 3288, 864.4223999999999]), 8)
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
    assert metadata.compound is True
    assert metadata.numberOfBlock == raw.metadata.numberOfBlock
    assert metadata.acquisitionMode == raw.metadata.acquisitionMode
    assert metadata.depth.depthFar == raw.metadata.depth.depthFar
    assert metadata.depth.depthNear == raw.metadata.depth.depthNear
    assert metadata.voxDim.dx == raw.metadata.voxDim.dx
    assert metadata.voxDim.dy == raw.metadata.voxDim.dy
    assert metadata.voxDim.dz == raw.metadata.voxDim.dz


@mark.filterwarnings("ignore::RuntimeWarning")
def test_invalid_blockEnd():
    raw = Raw(
        "./tests/data/" + "2DScan_v2.raw", "./tests/data/" + "2DScan_v2.hraw", 1, 100
    )
    assert raw.metadata.numberOfBlock == 9
    assert raw.data.shape[3] == 9


def test_raw_block_offset_with_multiple_rows(tmp_path):
    header_path = tmp_path / "sample.hraw"
    raw_path = tmp_path / "sample.raw"

    def encrypt(values, index):
        return np.asarray(values, dtype=float) * (1005 * index) + 72

    with h5py.File(header_path, "w") as header:
        header.create_dataset("F1", data=encrypt([[1]], 1))
        header.create_dataset("F2", data=encrypt([[2]], 2))
        header.create_dataset("F3", data=encrypt([[3]], 3))
        header.create_dataset("F4", data=encrypt([[4]], 4))
        header.create_dataset("F5", data=encrypt([[1, 2]], 5))
        header.create_dataset("F6", data=encrypt([[1, 2]], 6))
        header.create_dataset("F7", data=encrypt([[1, 2]], 7))
        header.create_dataset("F8", data=encrypt([[1, 2, 3]], 8))
        header.create_dataset("F9", data=encrypt([[2, 2, 1, 1, 1]], 9))
        header.create_dataset("F10", data=encrypt([[1]], 10))
        header.create_dataset("F11", data=encrypt([[2]], 11))
        header.create_dataset("F12", data=encrypt([[0]], 12))
        header.create_dataset("F13", data=np.asarray([[b"2Dscan"]]))

    block = np.zeros((2, 1, 2, 2, 1, 1, 1), dtype="<f4", order="F")
    block[0] = 1
    first_block = block.ravel(order="F")
    block[0] = 2
    second_block = block.ravel(order="F")
    np.concatenate((first_block, second_block)).tofile(raw_path)

    raw = Raw(str(raw_path), str(header_path), blockStart=2, blockEnd=2)

    assert np.all(raw.data == 2)
