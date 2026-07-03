from pyiconeus.io.base import read_bri
from tests.test_open import testDataPath
from pyiconeus.models.Roi import Roi
from pyiconeus.io.roi.bri_reader import bri_reader_binary, bri_reader_hdf5

def test_load_hdf5():
    roi_test: Roi = bri_reader_hdf5(testDataPath + "/roi_for_4DStacked.bri")
    assert roi_test is not None

def test_load_binary():
    roi_test: Roi = bri_reader_binary(testDataPath + "/roiread_binary.bri")
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
