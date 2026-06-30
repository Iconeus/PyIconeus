from pathlib import Path
from src.models.Scan import Scan
from src.models.Scan import VoxDim
from src.models.Scan import AcquisitionMode
from pyfus.io.files import _hdf52scan
from pyfus.scan.consolidation import consolidate_scan, _deconvolve_probe_path


def read_hdf5(filepath):
    scan = _hdf52scan(filepath)
    scan = consolidate_scan(scan)
    out_scan: Scan = Scan()
    out_scan.sizeX = scan.shape[0]
    out_scan.sizeY = scan.shape[1]
    out_scan.sizeZ = scan.shape[2]
    out_scan.nTime = scan.shape[3]
    out_scan.nPose = 1  # Always when consolidated
    match scan.modality:
        case "2D":
            out_scan.acquisitionMode = AcquisitionMode(0)
        case "2D+t":
            out_scan.acquisitionMode = AcquisitionMode(0)
        case "3D":
            out_scan.acquisitionMode = AcquisitionMode(1)
        case "3D+t":
            out_scan.acquisitionMode = AcquisitionMode(2)
    out_scan.voxDim = VoxDim(scan.voxdim[0], scan.voxdim[1], scan.voxdim[2], scan.dt, 0.0, 0.0)
    out_scan.integrationWindowDuration = scan.dt
    translations, rotations, _ = _deconvolve_probe_path(scan.get_qform())
    out_scan.probeToLabsTranslations = translations
    out_scan.probeToLabsRotations = rotations
    return out_scan


if __name__ == "__main__":
    scan = read_hdf5("./tests/data/4Dscan_1_StimVIS16__60_30_60_8_fus3D.source.scan")
    print(scan.sizeX)
    path = Path("./tests/data/4Dscan_1_StimVIS16__60_30_60_8_fus3D.source.scan")
    print(consolidate_scan(_hdf52scan(path)).voxdim)
    print(
        f"SizeX: {scan.sizeX}\nSizeY: {scan.sizeY}\nSizeZ: {scan.sizeZ}\nnTime: {scan.nTime}\nnPose: {scan.nPose}\n"
    )
