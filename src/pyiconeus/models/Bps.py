import h5py
import numpy as np

from ..utils.utils import _read_struct


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
                        self.data[i][j] = _read_struct(f, "<d")
        else:
            with h5py.File(filepath, "r") as f:
                dataset = f["BrainToLab"]
                if dataset.shape != (4, 4):
                    raise ValueError(
                        f"BrainToLab must have shape (4, 4), got {dataset.shape}"
                    )
                self.data: np.ndarray = dataset[:]
        if self.data.shape != (4, 4):
            raise ValueError(
                f"BrainToLab must have shape (4, 4), got {self.data.shape}"
            )
