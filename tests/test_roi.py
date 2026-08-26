# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np

import pyiconeus
from pyiconeus.io.base import read_bri


def test_load_hdf5():
    roi_test: pyiconeus.Roi = read_bri("./tests/data" + "/roi_for_4DStacked.bri")
    assert isinstance(roi_test, pyiconeus.Roi)


def test_load_binary():
    roi_test: pyiconeus.Roi = read_bri("./tests/data" + "/roiread_binary.bri")
    assert isinstance(roi_test, pyiconeus.Roi)


def test_roi_dispatch_version():
    roi_test_hdf5: pyiconeus.Roi = read_bri("./tests/data" + "/roi_for_4DStacked.bri")
    roi_test_binary: pyiconeus.Roi = read_bri("./tests/data" + "/roiread_binary.bri")
    print("\nRoi Hdf5")
    print(roi_test_hdf5)
    print("\nRoi binary")
    print(roi_test_binary)
    assert isinstance(roi_test_hdf5, pyiconeus.Roi)
    assert isinstance(roi_test_binary, pyiconeus.Roi)


def test_roi_values():
    roi_test: pyiconeus.Roi = read_bri("./tests/data" + "/Cortex.bri")
    assert roi_test.list[0].name == "Isocortex (L)"
    color = roi_test.list[0].color
    assert color[0] == float(112 / 255)
    assert color[1] == float(255 / 255)
    assert color[2] == float(113 / 255)
    assert roi_test.list[0].faces.shape == np.ndarray(shape=(10000, 3)).shape
    assert roi_test.list[0].vertices.shape == np.ndarray(shape=(4991, 3)).shape
    assert roi_test.list[1].name == "Isocortex (R)"
    color = roi_test.list[0].color
    assert color[0] == float(112 / 255)
    assert color[1] == float(255 / 255)
    assert color[2] == float(113 / 255)
    assert roi_test.list[1].faces.shape == np.ndarray(shape=(10000, 3)).shape
    assert roi_test.list[1].vertices.shape == np.ndarray(shape=(4991, 3)).shape
