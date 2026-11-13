# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

import pyiconeus


def test_open_scan_v2(data_path):
    scan = pyiconeus.open_path(
        data_path("4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan")
    )
    assert isinstance(scan, pyiconeus.Scan)
    scan = pyiconeus.open_path(data_path("2DScan_v2.source.scan"))
    assert isinstance(scan, pyiconeus.Scan)


def test_open_bps(data_path):
    bps = pyiconeus.open_path(data_path("Mouse.bps"))
    assert isinstance(bps, pyiconeus.Bps)


def test_open_bps_v2(data_path):
    bps = pyiconeus.open_path(
        data_path("4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.bps")
    )
    assert isinstance(bps, pyiconeus.Bps)


def test_open_roi(data_path):
    roi = pyiconeus.open_path(data_path("roi_for_4DStacked.bri"))
    assert isinstance(roi, pyiconeus.Roi)


def test_open_roi_binary(data_path):
    roi = pyiconeus.open_path(data_path("roiread_binary.bri"))
    assert isinstance(roi, pyiconeus.Roi)


def test_open_raw(data_path):
    raw = pyiconeus.open_path(data_path("2DScan_v2.raw"), data_path("2DScan_v2.hraw"))
    assert isinstance(raw, pyiconeus.Raw)
