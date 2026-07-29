from io import BufferedReader
import struct
import numpy as np
import numpy.typing as npt
import h5py

encoding = "utf-8"


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
    if h5py.check_string_dtype(hdf5_dataset.dtype).encoding == "utf-8":
        bytes_data = hdf5_dataset[()]
        strings = np.array(
            [b.decode("ascii") for b in bytes_data.flat], dtype=object
        ).reshape(bytes_data.shape)[0][0]
    else:
        # HDF5 ASCII strings
        bytes_data = hdf5_dataset[()][:]
        strings = str(bytes_data, 'utf-8')
    return strings


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
    print("Shape: " + str(hdf5_dataset.shape[0]) + "," + str(hdf5_dataset.shape[1]))
    print("Size: " + str(hdf5_dataset.size))
    print("Ndim: " + str(hdf5_dataset.ndim))
    print("Dtype: " + str(hdf5_dataset.dtype))
    print("Nbytes: " + str(hdf5_dataset.nbytes))
    print()


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
    stringSize = struct.unpack(format, f.read(bytes_size))[0]
    string = ""
    for _ in range(stringSize):
        string += str(struct.unpack("@s", f.read(1))[0], encoding)
    return string


def translationMatrix(dx: float, dy: float, dz: float) -> np.ndarray:
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


def scaleMatrix(sx: float, sy: float, sz: float) -> np.ndarray:
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


def decryptData(value: np.ndarray, n: int) -> np.ndarray:
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
    **arr** : numpy.ndarray
        Array to squeeze trailing unitary dimensions from.
    **initial** : int, optional
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


def rotation_xyz( theta: tuple[float, float, float] ):
    """
    Create a rotation matrix in xyz order using 'theta'

    Parameters
    ----------

    **theta**: float
        The degree of rotation in radians

    Returns
    -------

    np.ndarray
        The 4x4 rotation matrix
    """
    cx, cy, cz = np.cos(theta)
    sx,sy,sz = np.sin(theta)
    return np.array([
        [cy*cz, -cx*sz + cz*sx*sy, cx*cz*sy + sx*sz, 0],
        [cy*sz,  cx*cz + sx*sy*sz, cx*sy*sz - cz*sx, 0],
        [  -sy,             cy*sx,            cx*cy, 0],
        [    0,                 0,                0, 1]
    ],dtype=float)


def inverse_rotation_xyz( M ):
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
    if np.abs(M[2,0]) > 1.0:
        sy = -np.sign(M[2,0])
        y0 = sy*np.pi/2

        # arbitrarily set z=0
        z0 = 0 # so sz=0, cz=1

        # compute x = arctan2( M[0,1]/sy, M[02]/sy )
        x0 = np.arctan2( M[0,1]/sy, M[0,2]/sy )
        return np.array((x0,y0,z0))
    else:
        y0 = np.arcsin( -M[2,0] )
        c0 = np.cos(y0)

        x0 = np.arctan2( M[2,1]/c0, M[2,2]/c0 )

        z0 = np.arctan2( M[1,0]/c0, M[0,0]/c0 )
        return np.array((x0,y0,z0))
