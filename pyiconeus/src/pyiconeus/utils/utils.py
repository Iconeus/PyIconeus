import struct
import numpy as np
import h5py

encoding = "utf-8"


def hdf5_string_reader(hdf5_dataset):
    if h5py.check_string_dtype(hdf5_dataset.dtype).encoding == "utf-8":
        strings = hdf5_dataset[()]
    else:
        # HDF5 ASCII strings
        bytes_data = hdf5_dataset[()]
        strings = np.array(
            [b.decode("ascii") for b in bytes_data.flat], dtype=object
        ).reshape(bytes_data.shape)
    return strings


def hdf5_printer(hdf5_dataset):
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


def translationMatrix(dx, dy, dz):
    return np.array([[1, 0, 0, dx], [0, 1, 0, dy], [0, 0, 1, dz], [0, 0, 0, 1]])


def scaleMatrix(sx, sy, sz):
    return np.array([[sx, 0, 0, 0], [0, sy, 0, 0], [0, 0, sz, 0], [0, 0, 0, 1]])
