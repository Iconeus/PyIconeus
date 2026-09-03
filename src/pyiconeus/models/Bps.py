# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import os

import h5py
import numpy as np

from ..utils.utils import _read_struct, check_fourCC


class Bps:
    """
    Brain Positioning System, or BrainToLab is the affine matrix from the Brain space to the Lab space

    Attributes
    ----------

    data: np.ndarray (4, 4)
        The affine matrix
    """

    BPS_4CC_STR = "bps_"

    def __init__(self, filepath: str | os.PathLike[str]) -> None:
        if check_fourCC(filepath, self.BPS_4CC_STR):
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
                self.data = dataset[:]
        if self.data.shape != (4, 4):
            raise ValueError(
                f"BrainToLab must have shape (4, 4), got {self.data.shape}"
            )
