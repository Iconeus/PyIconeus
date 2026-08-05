from operator import inv
import h5py
import numpy as np
from pyiconeus.utils.utils import hdf5_printer, rotation_xyz, inverse_rotation_xyz
from pyiconeus import open_path


def test_hdf5_printer():
    with h5py.File("./tests/data/2DScan.source.scan") as f:
        hdf5_printer(f["Data"])
        assert True


def test_rotation_matrix():
    rotmatx = rotation_xyz((np.radians(90), 0, 0))
    x_rot_mat = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    assert np.allclose(rotmatx, x_rot_mat)
    rotmaty = rotation_xyz((0, np.radians(90), 0))
    y_rot_mat = np.array([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 1]])
    assert np.allclose(rotmaty, y_rot_mat)
    rotmatz = rotation_xyz((0, 0, np.radians(90)))
    z_rot_mat = np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    assert np.allclose(rotmatz, z_rot_mat)


def test_inverse_rotation_matrix():
    x_rot_mat = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    assert np.allclose(
        np.degrees(inverse_rotation_xyz(x_rot_mat)), np.array((90, 0, 0))
    )
    gimballPos = np.array(
        [
            [0, np.sin(0.5), np.cos(0.5), 0],
            [0, np.cos(0.5), -np.sin(0.5), 0],
            [-1, 0, 0, 0],
            [0, 0, 0, 1],
        ]
    )
    assert np.allclose(
        inverse_rotation_xyz(gimballPos), np.array((0.5, 1.57079633, 0.0))
    )

    gimballNeg = np.array(
        [
            [0, -np.sin(0.5), -np.cos(0.5), 0],
            [0, np.cos(0.5), -np.sin(0.5), 0],
            [1, 0, 0, 0],
            [0, 0, 0, 1],
        ]
    )
    assert np.allclose(
        inverse_rotation_xyz(gimballNeg), np.array((0.5, -1.57079633, 0.0))
    )

    eul = np.array((np.radians(45), np.radians(30), np.radians(60)))
    assert np.allclose(inverse_rotation_xyz(rotation_xyz(eul.tolist())), eul)
