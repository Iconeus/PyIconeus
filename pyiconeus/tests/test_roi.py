import numpy as np
from pyiconeus.io.base import read_bri
from tests.test_open import testDataPath
from pyiconeus.models.Roi import Roi, RoiColor


def test_load_hdf5():
    roi_test: Roi = read_bri(testDataPath + "/roi_for_4DStacked.bri")
    assert roi_test is not None


def test_load_binary():
    roi_test: Roi = read_bri(testDataPath + "/roiread_binary.bri")
    assert roi_test is not None


def test_roi_dispatch_version():
    roi_test_hdf5: Roi = read_bri(testDataPath + "/roi_for_4DStacked.bri")
    roi_test_binary: Roi = read_bri(testDataPath + "/roiread_binary.bri")
    print("\nRoi Hdf5")
    print(roi_test_hdf5)
    print("\nRoi binary")
    print(roi_test_binary)
    assert roi_test_hdf5 is not None
    assert roi_test_binary is not None


def test_roi_values():
    roi_test: Roi = read_bri(testDataPath + "/Cortex.bri")
    assert roi_test.list[0].name == "Isocortex (L)"
    color: RoiColor =  roi_test.list[0].color
    assert color.r == float(112 / 256)
    assert color.g == float(255 / 256)
    assert color.b == float(113 / 256)
    assert roi_test.list[0].faces.shape == np.ndarray(shape=(10000, 3)).shape
    assert roi_test.list[0].vertices.shape == np.ndarray(shape=(4991, 3)).shape
    assert roi_test.list[1].name == "Isocortex (R)"
    color: RoiColor =  roi_test.list[0].color
    assert color.r == float(112 / 256)
    assert color.g == float(255 / 256)
    assert color.b == float(113 / 256)
    assert roi_test.list[1].faces.shape == np.ndarray(shape=(10000, 3)).shape
    assert roi_test.list[1].vertices.shape == np.ndarray(shape=(4991, 3)).shape

if __name__ == '__main__':
    test_roi_values()
