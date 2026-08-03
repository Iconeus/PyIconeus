import h5py
import numpy as np
from struct import unpack


class Bps:
    """
    Brain Positioning System, or BrainToLab is the affine matrix from the Brain space to the Lab space

    Attributes
    ----------

    data: np.ndarray (4, 4)
        The affine matrix
    """
    def __init__(self, filepath: str, is_binary: bool = False) -> None:
        if is_binary:
            with open(filepath, "rb") as f:
                self.data: np.ndarray = np.ndarray(shape=(4, 4), dtype=float)
                f.seek(12)
                for i in range(4):
                    for j in range(4):
                        self.data[i][j] = unpack("<d", f.read(8))[0]
        else:
            f = h5py.File(filepath, "r")
            self.data: np.ndarray = f["BrainToLab"][:]
