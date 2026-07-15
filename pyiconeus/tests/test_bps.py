import numpy as np
from tests.test_open import testDataPath
from pyiconeus.models.Scan import Scan
from pyiconeus.models.Bps import Bps
from pyiconeus.io.base import read_bps


def test_bps_load():
    bps = read_bps(testDataPath + "/Mouse.bps")
    assert bps is not None


def test_print_bps():
    bps = read_bps(testDataPath + "/Mouse.bps")
    # Add --capture=no stdout to see BPS
    assert bps is not None


def test_assign_bps():
    scan: Scan = Scan(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan", True
    )
    bps: Bps = read_bps(testDataPath + "/Mouse.bps")
    scan.bps = bps
    assert scan.bps is not None


def test_load_bps_v2():
    bps = read_bps(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.bps"
    )
    assert bps is not None


def test_bps_v2_data():
    data_true = np.array(
        [
            [
                0.000004845665888,
                0.003799318538138,
                -0.0001917964938,
                -0.008609746195099,
            ],
            [
                -0.00368395440299,
                -0.000078617861918,
                0.000046574948263,
                -0.001069632271113,
            ],
            [
                -0.00002303562752,
                0.000195067316877,
                0.003693082933202,
                -0.045093259666531,
            ],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    bps: Bps = read_bps(
        testDataPath + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.bps"
    )
    print("data: ")
    print(data_true)
    print("bps data: ")
    print(bps.data)
    assert np.allclose(
        bps.data, data_true
    )  # Numpy round too large values, check if values are close enough


if __name__ == "__main__":
    test_assign_bps()
