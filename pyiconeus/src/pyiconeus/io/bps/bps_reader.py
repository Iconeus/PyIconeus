import struct
from ...models.Bps import Bps
import numpy as np
import h5py

def read_binary_bps(filepath):
    with open(filepath, 'rb') as f:
        data = np.ndarray(shape=(4, 4), dtype=float)
        f.seek(12)
        for i in range(4):
            for j in range(4):
                data[i][j] = struct.unpack('@d', f.read(8))[0]
        bps = Bps(data)
        return bps

def read_h5_bps(filepath):
    f = h5py.File(filepath, "r")
    data: np.ndarray = f["BrainToLab"][:]
    bps = Bps(data)
    return bps


if __name__ == "__main__":
    print(read_h5_bps("tests\\data\\Mouse.bps"))
