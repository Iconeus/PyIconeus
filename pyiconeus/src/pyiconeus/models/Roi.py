import numpy as np


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
    def __init__(self):
        self.list: list[RoiElements] = []

    def __repr__(self): ...
    def __str__(self):
        ret: str = f"Roi: {len(self.list)}\n"
        for roiElement in self.list:
            ret += f"{roiElement}"
        return ret


class RoiColor:
    def __init__(self, r: float, g: float, b: float):
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self): ...
    def __str__(self):
        return f"R: {self.r}, G: {self.g}, B: {self.b}"


class RoiElements:
    def __init__(
        self, color: RoiColor, vertices: np.ndarray, faces: np.ndarray, name: str
    ):
        self.name = name
        self.vertices = vertices
        self.faces = faces
        self.color = color

    def __repr__(self): ...
    def __str__(self):
        return f"{self.name}:\n\tColor: {self.color}\n\tVertices Count: {len(self.vertices)}\n\tFaces count: {len(self.faces)}\n"
