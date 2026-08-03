import h5py
from pyiconeus.utils.utils import hdf5_printer
from pyiconeus import open_path

def test_hdf5_printer():
    with h5py.File("./tests/data/2DScan.source.scan") as f:
        hdf5_printer(f["Data"])
        assert True

