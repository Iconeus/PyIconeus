# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import h5py
import warnings
import os
from numbers import Integral

from ..utils.utils import decrypt_data, hdf5_string_reader
from .Scan import Depth, VoxDim


def _first_value(value: np.ndarray) -> float:
    return float(np.asarray(value).reshape(-1)[0])


class Raw:
    """
    Raw class contains the metadata of the acquisition and its raw data

    Attributes
    ----------

    **metadata**: Raw.Metadata
        The metadata of the acquisition
    **data**: np.ndarray
        The raw data of the acquisition
    """

    class MetaData:
        """
        Metadata of the raw acquisition

        Attributes
        ----------

        **transmitFrequency**: float
            The transmit frequency of the acquisition

        **prf**: float
            The pulse repetition frequency

        **speedOfSound**: float
            The speed of sound

        **frameRate**: float
            Frame rate of the acquisition

        **receiveAperture**: np.ndarray
            Receive Aperture

        **depth**: Scan.Depth
            Near and Far depth

        **flatAngles**: np.ndarray
            Angles of the probe during the acquisition

        **voxDim**: Scan.VoxDim
            VoxDim data

        **blockDim**: np.ndarray
            BlockDim data

        **compound**: bool
            True if the images are compounded, False otherwise

        **numberOfBlock**: int
            Number of blocks

        **isEncrypted**: bool
            Is the data encrypted or not

        **acquisitionMode**: *str*
            Type of acquisition
        """

        def __init__(self, fileheader) -> None:
            with h5py.File(fileheader, "r") as h5:
                self.transmitFrequency: float = _first_value(decrypt_data(h5["F1"], 1))
                self.prf: float = _first_value(decrypt_data(h5["F2"], 2))
                self.speedOfSound: float = _first_value(decrypt_data(h5["F3"], 3))
                self.frameRate: float = _first_value(decrypt_data(h5["F4"], 4))
                self.receiveAperture: np.ndarray = decrypt_data(h5["F5"], 5)
                self.flatAngles: np.ndarray = decrypt_data(h5["F7"], 7)
                self.blockDim: np.ndarray = decrypt_data(h5["F9"], 9)
                self.compound: bool = bool(_first_value(decrypt_data(h5["F10"], 10)))
                self.numberOfBlock: int = int(_first_value(decrypt_data(h5["F11"], 11)))
                self.acquisitionMode: str = hdf5_string_reader(h5["F13"])
                depthData: np.ndarray = decrypt_data(h5["F6"], 6)
                voxDimData: np.ndarray = decrypt_data(h5["F8"], 8)
                depth = np.asarray(depthData).reshape(-1)
                if depth.size < 2:
                    raise ValueError("RAW depth must contain two values")
                self.depth = Depth()
                self.depth.depthNear = float(depth[0])
                self.depth.depthFar = float(depth[1])
                vox_dim = np.asarray(voxDimData).reshape(-1)
                if vox_dim.size < 3:
                    raise ValueError("RAW voxDim must contain three dimensions")
                self.voxDim = VoxDim(vox_dim[0], vox_dim[1], vox_dim[2])
                self.isEncrypted: bool = bool(_first_value(decrypt_data(h5["F12"], 12)))

    def __init__(
        self,
        filepath: str | os.PathLike[str],
        file_header: str | os.PathLike[str],
        blockStart: int = 1,
        blockEnd: int = 1,
    ) -> None:
        self.metadata = Raw.MetaData(file_header)
        if (
            not isinstance(blockStart, Integral)
            or isinstance(blockStart, bool)
            or not isinstance(blockEnd, Integral)
            or isinstance(blockEnd, bool)
        ):
            raise TypeError("blockStart and blockEnd must be integers")
        block_dimensions = np.asarray(self.metadata.blockDim).reshape(-1)
        if block_dimensions.size < 5:
            raise ValueError("RAW blockDim must contain five dimensions")
        nCompound, nFramesPerBlock, sizeX, sizeY, sizeZ = tuple(
            int(block_dimensions[index]) for index in (3, 4, 0, 1, 2)
        )
        if min(nCompound, nFramesPerBlock, sizeX, sizeY, sizeZ) <= 0:
            raise ValueError("RAW dimensions must be positive")
        if self.metadata.numberOfBlock <= 0:
            raise ValueError("RAW numberOfBlock must be positive")
        if blockEnd < blockStart:
            raise RuntimeError("blockEnd must be greater or equal to blockStart")
        if blockStart < 1 or blockStart > self.metadata.numberOfBlock:
            raise ValueError("blockStart is outside the available RAW blocks")
        if blockEnd > self.metadata.numberOfBlock:
            warnings.warn(
                "Passed blockEnd was greater than the total number of blocks; it was clamped.",
                RuntimeWarning,
                stacklevel=2,
            )
        blockEnd = min(blockEnd, self.metadata.numberOfBlock)
        nBlockToSkip = blockStart - 1
        nBlockToRead = blockEnd - nBlockToSkip
        n_elements = int(
            2 * sizeX * sizeY * sizeZ * nCompound * nFramesPerBlock * nBlockToRead
        )
        block_size = 2 * sizeX * sizeY * sizeZ * nCompound * nFramesPerBlock * 4
        with open(filepath, "rb") as f:
            if self.metadata.isEncrypted:
                f.seek(117)
            f.seek(nBlockToSkip * block_size, 1)
            expected_bytes = n_elements * np.dtype("<f4").itemsize
            remaining_bytes = os.fstat(f.fileno()).st_size - f.tell()
            if remaining_bytes < expected_bytes:
                raise OSError(
                    f"RAW file is truncated: expected {expected_bytes} data bytes, "
                    f"found {max(remaining_bytes, 0)}"
                )
            iQt: np.ndarray = np.fromfile(f, dtype="<f4", count=n_elements)
        if iQt.size != n_elements:
            raise OSError(f"RAW file contains {iQt.size} values, expected {n_elements}")
        iQt = iQt.reshape(
            (2, sizeZ, sizeY, sizeX, nCompound, nFramesPerBlock, nBlockToRead),
            order="F",
        )
        iQblock: np.ndarray = iQt[0, ...] + 1j * iQt[1, ...]
        iQblock = np.squeeze(iQblock)

        self.data: np.ndarray = iQblock
