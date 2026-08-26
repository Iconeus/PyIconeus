# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import struct
from io import BufferedReader

import h5py
import numpy as np
import numpy.typing as npt

_MAX_BINARY_STRING_SIZE = 16 * 1024 * 1024


def _read_exact(stream: BufferedReader, size: int) -> bytes:
    if size < 0:
        raise ValueError("size must be non-negative")
    offset = stream.tell()
    data = stream.read(size)
    if len(data) != size:
        raise OSError(
            f"Unexpected end of file at offset {offset}: expected {size} bytes, got {len(data)}"
        )
    return data


def _read_struct(stream: BufferedReader, format: str):
    return struct.unpack(format, _read_exact(stream, struct.calcsize(format)))[0]


def hdf5_string_reader(hdf5_dataset: h5py.Dataset) -> str:
    """
    Util function used to read an HDF5 string element depending of the internal type

    Parameters
    ----------

    **hdf5_dataset**: h5py.Dataset
        The HDF5 string element

    Returns
    -------

    str
        The decode string
    """
    value = hdf5_dataset[()]
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return ""
        value = value.reshape(-1)[0]
    if isinstance(value, np.bytes_):
        value = value.tobytes()
    if isinstance(value, bytes):
        return value.decode("utf-8").rstrip("\x00").strip()
    return str(value).rstrip("\x00").strip()


def hdf5_printer(hdf5_dataset: h5py.Dataset) -> None:
    """
    Pretty print of a hdf5 dataset parameters

    Parameters
    ----------

    **hdf5_dataset**: h5py.Dataset
        The HDF5 Dataset to display

    Returns
    -------

    None
    """
    print("HDF5 element:")
    print(f"Shape: {hdf5_dataset.shape}")
    print(f"Size: {hdf5_dataset.size}")
    print(f"Ndim: {hdf5_dataset.ndim}")
    print(f"Dtype: {hdf5_dataset.dtype}")
    print(f"Nbytes: {hdf5_dataset.nbytes}")


def read_string_binary(f: BufferedReader, format: str, bytes_size: int) -> str:
    """
    String reader for Iconeus binary files

    Parameters
    ----------

    **f**: BufferedReader
        Binary file stream
    **format**: str
        String format for struct.unpack. Tells the type of the element to read
    **bytes_size**: int
        Number of element of type 'format' to read

    Returns
    -------

    str
        The resulted string of size 'bytes_size'
    """
    string_size = struct.unpack(format, _read_exact(f, bytes_size))[0]
    if string_size > _MAX_BINARY_STRING_SIZE:
        raise ValueError(f"binary string is too large: {string_size} bytes")
    return _read_exact(f, string_size).decode("utf-8").strip("\x00 ")


def translation_matrix(dx: float, dy: float, dz: float) -> np.ndarray:
    """
    Create a 4x4 tform with given translation

    Parameters
    ----------

    **dx**: float
        x-component of the translation
    **dy**: float
        y-component of the translation
    **dz**: float
        z-component of the translation

    Returns
    -------

    np.ndarray
        The 4x4 tform
    """
    return np.array([[1, 0, 0, dx], [0, 1, 0, dy], [0, 0, 1, dz], [0, 0, 0, 1]])


def scale_matrix(sx: float, sy: float, sz: float) -> np.ndarray:
    """
    Create a 4x4 tform with given scale components

    Parameters
    ----------

    **dx**: float
        x-component of the scaling
    **dy**: float
        y-component of the scaling
    **dz**: float
        z-component of the scaling

    Returns
    -------

    np.ndarray
        The 4x4 tform
    """
    return np.array([[sx, 0, 0, 0], [0, sy, 0, 0], [0, 0, sz, 0], [0, 0, 0, 1]])


def decrypt_data(value: np.ndarray, n: int) -> np.ndarray:
    """
    Util function to decrypt raw data that have been encrypted in first versions of '.raw' files

    Parameters
    ----------

    **value**: np.ndarray
        The crypted value
    **n**: int
        The index of the element in the hdf5 to be decrypted

    Returns
    -------

    **nbr**: np.ndarray
        The decrypted value
    """
    value_array = np.asarray(value, dtype=float)
    if value_array.size == 1:
        nbrc: np.ndarray = value_array.reshape(-1)[0]
    else:
        nbrc = value_array
    nbr: np.ndarray = nbrc.copy()
    if nbrc.ndim < 3:
        nbr = (nbrc - 72) / (1005 * n)
    return np.asarray(nbr)


def transform_points_forward(tform: npt.NDArray, points: npt.NDArray) -> npt.NDArray:
    """Applies a affine transform to 3D-points

    Equivalent of MATLAB's 'affine3d.transformPointsForward', with regards of numpy's convention (column vector):
    `tform @ [x, y, z, 1]`

    Parameters
    ----------
    **tform** : (4, 4) ndarray
        Homogenous affine matrix
    **points** : (N, 3) ndarray
        Points to transform

    Returns
    -------
    (N, 3) ndarray
        Transformed points
    """
    return points @ tform[:3, :3].T + tform[:3, 3]


def rotation_xyz(theta: tuple[float, float, float]):
    """
    Create a rotation matrix in xyz order using 'theta'

    Parameters
    ----------

    **theta**: tuple[float, float, float]
        The euler angles of a rotation in radians

    Returns
    -------

    np.ndarray
        The 4x4 rotation matrix
    """
    cx, cy, cz = np.cos(theta)
    sx, sy, sz = np.sin(theta)
    return np.array(
        [
            [cy * cz, -cx * sz + cz * sx * sy, cx * cz * sy + sx * sz, 0],
            [cy * sz, cx * cz + sx * sy * sz, cx * sy * sz - cz * sx, 0],
            [-sy, cy * sx, cx * cy, 0],
            [0, 0, 0, 1],
        ],
        dtype=float,
    )


def inverse_rotation_xyz(M):
    """
    Computes the vector of euler angles from a rotation matrix

    Parameters
    ----------

    **M**: np.ndarray
        The rotation matrix

    Returns
    -------

    np.ndarray: (x, y, z)
        Vector of euler angles
    """
    if M[2, 0] <= -1.0 + 1e-5:
        y0 = np.pi / 2
        z0 = 0.0
        x0 = np.arctan2(M[0, 1], M[0, 2])
        return np.array((x0, y0, z0))

    elif M[2, 0] >= 1.0 - 1e-5:
        y0 = -np.pi / 2
        z0 = 0.0
        x0 = np.arctan2(-M[0, 1], -M[0, 2])
        return np.array((x0, y0, z0))
    else:
        y0 = np.arcsin(-M[2, 0])
        c0 = np.cos(y0)

        x0 = np.arctan2(M[2, 1] / c0, M[2, 2] / c0)

        z0 = np.arctan2(M[1, 0] / c0, M[0, 0] / c0)
        return np.array((x0, y0, z0))
