import struct
import numpy as np
import numpy.typing as npt
import h5py

encoding = "utf-8"


def hdf5_string_reader(hdf5_dataset) -> str:
    if h5py.check_string_dtype(hdf5_dataset.dtype).encoding == "utf-8":
        bytes_data = hdf5_dataset[()]
        strings = np.array(
            [b.decode("ascii") for b in bytes_data.flat], dtype=object
        ).reshape(bytes_data.shape)[0][0]
    else:
        # HDF5 ASCII strings
        bytes_data = hdf5_dataset[()]
        strings = np.array(
            [b.decode("ascii") for b in bytes_data.flat], dtype=object
        ).reshape(bytes_data.shape)
    return strings


def hdf5_printer(hdf5_dataset) -> None:
    print("HDF5 element:")
    print("Shape: " + str(hdf5_dataset.shape[0]) + "," + str(hdf5_dataset.shape[1]))
    print("Size: " + str(hdf5_dataset.size))
    print("Ndim: " + str(hdf5_dataset.ndim))
    print("Dtype: " + str(hdf5_dataset.dtype))
    print("Nbytes: " + str(hdf5_dataset.nbytes))
    print()


def read_string_binary(f, format, bytes_size) -> str:
    stringSize = struct.unpack(format, f.read(bytes_size))[0]
    rep = ""
    for _ in range(stringSize):
        rep += str(struct.unpack("@s", f.read(1))[0], encoding)
    return rep


def translationMatrix(dx, dy, dz) -> np.ndarray:
    return np.array([[1, 0, 0, dx], [0, 1, 0, dy], [0, 0, 1, dz], [0, 0, 0, 1]])


def scaleMatrix(sx, sy, sz) -> np.ndarray:
    return np.array([[sx, 0, 0, 0], [0, sy, 0, 0], [0, 0, sz, 0], [0, 0, 0, 1]])


def decryptData(value, n: int) -> np.ndarray:
    if value.shape[0] == 1:
        nbrc: np.ndarray = np.asarray(value, dtype=float)[0]
    else:
        nbrc = np.asarray(value, dtype=float)
    nbr: np.ndarray = nbrc.copy()
    if nbrc.ndim < 3:
        nbr: np.ndarray = (nbrc - 72) / (1005 * n)
    return nbr


def squeeze_trailing(arr: npt.NDArray, initial: int = 0) -> npt.NDArray:
    """Squeeze trailing unitary dimensions.

    Parameters
    ----------
    arr : numpy.ndarray
        Array to squeeze trailing unitary dimensions from.
    initial : int, optional
        Axes up to index `initial` (not included) will not be squeezed even if they're
        trailing unitary. Default is 0.

    Returns
    -------
    numpy.ndarray
        The squeezed array.
    """
    non_unitary_dims = (np.asarray(arr.shape) != 1).nonzero()[0]
    last_non_unitary_dim = non_unitary_dims[-1] if non_unitary_dims.size > 0 else 0
    new_shape = arr.shape[:initial] + arr.shape[initial : (last_non_unitary_dim + 1)]

    arr.reshape(new_shape)
    return arr


def transform_points_forward(tform: npt.NDArray, points: npt.NDArray) -> npt.NDArray:
    """Applique une transformation affine à des points 3D.

    Équivalent de `affine3d.transformPointsForward` (MATLAB), avec la convention
    numpy (vecteur colonne) : `tform @ [x, y, z, 1]`.

    Parameters
    ----------
    tform : (4, 4) ndarray
        Matrice affine homogène.
    points : (N, 3) ndarray
        Points à transformer.

    Returns
    -------
    (N, 3) ndarray
        Points transformés.
    """
    # homogeneous = np.hstack([points, np.ones((points.shape[0], 1))])
    return points @ tform[:3, :3].T + tform[:3, 3]
    # return (tform @ homogeneous.T).T[:, :3]
