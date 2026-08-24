# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pyiconeus
from pyiconeus.io.base import read_bps


def test_bps_load():
    bps: pyiconeus.Bps = read_bps("./tests/data" + "/Mouse.bps")
    assert isinstance(bps, pyiconeus.Bps)
    assert bps.data.shape == np.ndarray((4, 4)).shape


def test_assign_bps():
    scan: pyiconeus.Scan = pyiconeus.Scan(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan", True
    )
    bps: pyiconeus.Bps = read_bps("./tests/data" + "/Mouse.bps")
    scan.bps = bps
    assert isinstance(bps, pyiconeus.Bps)


def test_load_bps_v2():
    bps = read_bps(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.bps"
    )
    assert isinstance(bps, pyiconeus.Bps)
    assert bps.data.shape == np.ndarray((4, 4)).shape


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
    bps: pyiconeus.Bps = read_bps(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.bps"
    )
    assert np.allclose(bps.data, data_true)

