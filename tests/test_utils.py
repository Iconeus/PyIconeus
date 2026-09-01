# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import h5py
import numpy as np

from pyiconeus.utils.consolidation import theoretical_time_indices
from pyiconeus.utils.utils import (
    check_fourCC,
    hdf5_printer,
    hdf5_string_reader,
    inverse_rotation_xyz,
    rotation_xyz,
)


def test_check_fourCC():
    assert check_fourCC(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan", "scan"
    )


def test_hdf5_printer():
    with h5py.File("./tests/data/2DScan.source.scan") as f:
        hdf5_printer(f["Data"])
        assert True


def test_hdf5_string_reader_variants(tmp_path):
    path = tmp_path / "strings.h5"
    with h5py.File(path, "w") as file:
        file.create_dataset(
            "scalar", data="café", dtype=h5py.string_dtype(encoding="utf-8")
        )
        file.create_dataset("array", data=np.asarray([["value"]], dtype="S8"))
        assert hdf5_string_reader(file["scalar"]) == "café"
        assert hdf5_string_reader(file["array"]) == "value"


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


def test_theoretical_time_indices():
    times = np.array([0.01, 0.02, 0.03])

    assert np.array_equal(
        theoretical_time_indices(times, 0.01, 0.01), np.array([0, 1, 2])
    )

    eul = np.array((np.radians(45), np.radians(30), np.radians(60)))
    assert np.allclose(inverse_rotation_xyz(rotation_xyz(eul.tolist())), eul)
