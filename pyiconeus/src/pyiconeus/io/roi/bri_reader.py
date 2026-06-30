import struct
import h5py
import numpy as np
from src.models.Roi import Roi
from src.models.Roi import RoiColor
from src.utils.utils import hdf5_string_reader, read_string_binary
from src.models.Roi import RoiElements


def bri_reader_hdf5(filepath) -> Roi:
    roi_output: Roi = Roi()
    with h5py.File(filepath, "r") as f:
        for roiElementName in f["ROI"]:
            roiElement: h5py.Dataset = f["ROI"][roiElementName]
            name: str = hdf5_string_reader(roiElement["label"])
            color: RoiColor = RoiColor(
                roiElement["color"][0][0] / 256,
                roiElement["color"][0][1] / 256,
                roiElement["color"][0][2] / 256
            )
            faces: np.ndarray = roiElement["faces"][:]
            vertices: np.ndarray = roiElement["vertices"][:]
            roi_output.list.append(RoiElements(color, vertices, faces, name))
    return roi_output


def bri_reader_binary(filepath) -> Roi:
    roi_output: Roi = Roi()
    with open(filepath, "rb") as f:
        f.seek(12)
        roi_count = struct.unpack("@L", f.read(4))[0]
        for _ in range(roi_count):
            # Vertices
            vertices_count: int = struct.unpack("@L", f.read(4))[0]
            vertices: np.ndarray = np.ndarray(shape=(vertices_count, 3))
            for i in range(vertices_count):
                vertices[i][0] = struct.unpack("@d", f.read(8))[0]
                vertices[i][1] = struct.unpack("@d", f.read(8))[0]
                vertices[i][2] = struct.unpack("@d", f.read(8))[0]

            # Triangles
            indices_count: int = struct.unpack("@L", f.read(4))[0]
            triangles: np.ndarray = np.ndarray(shape=(indices_count, 3))
            for i in range(indices_count):
                triangles[i][0] = int(struct.unpack("@L", f.read(4))[0])
                triangles[i][1] = int(struct.unpack("@L", f.read(4))[0])
                triangles[i][2] = int(struct.unpack("@L", f.read(4))[0])
            color = RoiColor(
                struct.unpack("@f", f.read(4))[0],
                struct.unpack("@f", f.read(4))[0],
                struct.unpack("@f", f.read(4))[0],
            )
            label: str = read_string_binary(f, '@L', 4)
            roi_output.list.append(RoiElements(color, vertices, triangles, label))
    return roi_output

if __name__ == "__main__":
    print(bri_reader_binary("./tests/data/roiread_binary.bri"))
    print(bri_reader_hdf5("./tests/data/roi_for_4DStacked.bri"))
