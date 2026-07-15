import h5py
import numpy as np
from ..utils.utils import read_string_binary, hdf5_string_reader
from struct import unpack


# ROI
# Extension: .bri
# HDF5 and Binary file
#
# Each ROI file contains one folder containing different ROIs
# ROI:
# Color: R, G, B elements
# Label: The name or the roi
# Vertices: Array of 3-Dimensional vertices
# Faces: Array of vertex indices composing the volume triangles (name: triangles in binary version)
class Roi:
    def __init__(self, filepath, is_binary: bool):
        self.list: list[RoiElements] = []
        if is_binary:
            with open(filepath, "rb") as f:
                f.seek(12)
                roi_count: int = unpack("@L", f.read(4))[0]
                for _ in range(roi_count):
                    # Vertices
                    vertices_count: int = unpack("@L", f.read(4))[0]
                    vertices: np.ndarray = np.ndarray(shape=(vertices_count, 3))
                    for i in range(vertices_count):
                        vertices[i][0] = unpack("@d", f.read(8))[0]
                        vertices[i][1] = unpack("@d", f.read(8))[0]
                        vertices[i][2] = unpack("@d", f.read(8))[0]

                    # Triangles
                    indices_count: int = unpack("@L", f.read(4))[0]
                    triangles: np.ndarray = np.ndarray(
                        shape=(indices_count, 3), dtype=int
                    )
                    for i in range(indices_count):
                        triangles[i][0] = unpack("@L", f.read(4))[0]
                        triangles[i][1] = unpack("@L", f.read(4))[0]
                        triangles[i][2] = unpack("@L", f.read(4))[0]
                    color: RoiColor = RoiColor(
                        float(unpack("@f", f.read(4))[0]),
                        float(unpack("@f", f.read(4))[0]),
                        float(unpack("@f", f.read(4))[0]),
                    )
                    label: str = read_string_binary(f, "@L", 4)
                    self.list.append(RoiElements(color, vertices, triangles, label))
        else:
            with h5py.File(filepath, "r") as f:
                for roiElementName in f["ROI"]:
                    roiElement: h5py.Dataset = f["ROI"][roiElementName]
                    name: str = hdf5_string_reader(roiElement["label"])
                    color: RoiColor = RoiColor(
                        float(roiElement["color"][0][0]) / 256,
                        float(roiElement["color"][0][1]) / 256,
                        float(roiElement["color"][0][2]) / 256,
                    )
                    faces: np.ndarray = roiElement["faces"][:]
                    vertices: np.ndarray = roiElement["vertices"][:]
                    self.list.append(RoiElements(color, vertices, faces, name))

    def __repr__(self): ...
    def __str__(self):
        ret: str = f"Roi: {len(self.list)}\n"
        for roiElement in self.list:
            ret += f"{roiElement}"
        return ret


class RoiColor:
    def __init__(self, r: float, g: float, b: float):
        self.r: float = r
        self.g: float = g
        self.b: float = b

    def __str__(self) -> str:
        return f"R: {self.r}, G: {self.g}, B: {self.b}"

    __repr__ = __str__


class RoiElements:
    def __init__(
        self, color: RoiColor, vertices: np.ndarray, faces: np.ndarray, name: str
    ):
        self.name: str = name
        self.vertices: np.ndarray = vertices
        self.faces: np.ndarray = faces
        self.color: RoiColor = color

    def __repr__(self): ...
    def __str__(self):
        return f"{self.name}:\n\tColor: {self.color}\n\tVertices Count: {len(self.vertices)}\n\tFaces count: {len(self.faces)}\n"
