# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import os

import h5py
import numpy as np

from ..utils.utils import (
    _read_struct,
    check_fourCC,
    hdf5_string_reader,
    read_string_binary,
)

_MAX_ROI_COUNT = 100_000
_MAX_MESH_ELEMENTS = 10_000_000


class Roi:
    """
    Region of Interest are 3D shapes, from an Atlas or created by the user.
    The Roi class contains a list of RoiElements.

    Attributes
    ----------

    color: RoiColor
        The displayed color of the Roi

    label: str
        The name of the Roi

    vertices: np.ndarray (N, 3)
        The points in Brain space of the volume

    faces: np.ndarray (N, 3)
        Each row contains the indices of the vertices composing a triangle of the volume
    """

    ROI_4CC_STR = "bri_"

    def __init__(self, filepath: str | os.PathLike[str]):
        self.list: list[RoiElements] = []
        if check_fourCC(filepath, self.ROI_4CC_STR):
            with open(filepath, "rb") as f:
                f.seek(12)
                roi_count: int = _read_struct(f, "<L")
                if roi_count > _MAX_ROI_COUNT:
                    raise ValueError(f"ROI count is too large: {roi_count}")
                for _ in range(roi_count):
                    vertices_count: int = _read_struct(f, "<L")
                    if vertices_count > _MAX_MESH_ELEMENTS:
                        raise ValueError(f"vertex count is too large: {vertices_count}")
                    vertices: np.ndarray = np.empty(shape=(vertices_count, 3))
                    for i in range(vertices_count):
                        vertices[i][0] = _read_struct(f, "<d")
                        vertices[i][1] = _read_struct(f, "<d")
                        vertices[i][2] = _read_struct(f, "<d")

                    indices_count: int = _read_struct(f, "<L")
                    if indices_count > _MAX_MESH_ELEMENTS:
                        raise ValueError(f"face count is too large: {indices_count}")
                    triangles: np.ndarray = np.empty(
                        shape=(indices_count, 3), dtype=np.int64
                    )
                    for i in range(indices_count):
                        triangles[i][0] = _read_struct(f, "<L")
                        triangles[i][1] = _read_struct(f, "<L")
                        triangles[i][2] = _read_struct(f, "<L")
                    if triangles.size and triangles.max() >= vertices_count:
                        raise ValueError("ROI face index is outside the vertices array")
                    color: tuple[float, ...] = (
                        float(_read_struct(f, "<f")),
                        float(_read_struct(f, "<f")),
                        float(_read_struct(f, "<f")),
                    )
                    label: str = read_string_binary(f, "<L", 4)
                    self.list.append(RoiElements(color, vertices, triangles, label))
        else:
            with h5py.File(filepath, "r") as f:
                roi_group = f["ROI"]
                if len(roi_group) > _MAX_ROI_COUNT:
                    raise ValueError(f"ROI count is too large: {len(roi_group)}")
                for roiElementName in roi_group:
                    roiElement: h5py.Dataset = f["ROI"][roiElementName]
                    name: str = hdf5_string_reader(roiElement["label"])
                    color_values = np.asarray(roiElement["color"][:]).reshape(-1)
                    if color_values.size < 3:
                        raise ValueError("ROI color must contain at least three values")
                    color = tuple(float(value) / 255 for value in color_values[:3])
                    vertices_dataset = roiElement["vertices"]
                    faces_dataset = roiElement["faces"]
                    if vertices_dataset.ndim != 2 or vertices_dataset.shape[1] != 3:
                        raise ValueError("ROI vertices must have shape (N, 3)")
                    if vertices_dataset.shape[0] > _MAX_MESH_ELEMENTS:
                        raise ValueError("vertex count is too large")
                    if faces_dataset.ndim != 2 or faces_dataset.shape[1] != 3:
                        raise ValueError("ROI faces must have shape (N, 3)")
                    if faces_dataset.shape[0] > _MAX_MESH_ELEMENTS:
                        raise ValueError("face count is too large")
                    vertices = np.asarray(vertices_dataset[:])
                    faces: np.ndarray = np.asarray(faces_dataset[:])
                    faces = faces.astype(np.int64, copy=False)
                    if faces.size and (
                        faces.min() < 1 or faces.max() >= vertices.shape[0] + 1
                    ):
                        raise ValueError("ROI face index is outside the vertices array")
                    faces = faces - 1
                    self.list.append(RoiElements(color, vertices, faces, name))

    def __str__(self) -> str:
        return f"Roi: {len(self.list)}\n" + "".join(map(str, self.list))

    __repr__ = __str__


class RoiElements:
    def __init__(
        self,
        color: tuple[float, ...],
        vertices: np.ndarray,
        faces: np.ndarray,
        name: str,
    ):
        self.name: str = name
        self.vertices: np.ndarray = vertices
        self.faces: np.ndarray = faces
        self.color: tuple[float, ...] = color

    def __str__(self) -> str:
        return f"{self.name}:\n\tColor: {self.color}\n\tVertices Count: {len(self.vertices)}\n\tFaces count: {len(self.faces)}\n"

    __repr__ = __str__
