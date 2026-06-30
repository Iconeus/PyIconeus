from ...models.Bps import Bps
import numpy as np
import h5py


def read_h5_bps(filepath):
    f = h5py.File(filepath, "r")
    data: np.ndarray = f["BrainToLab"][:]
    bps = Bps(data)
    return bps


if __name__ == "__main__":
    print(read_h5_bps("tests\\data\\Mouse.bps"))
