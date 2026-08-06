import pyiconeus

# Scan open
def test_open_scan_v2():
    scan = pyiconeus.open_path(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.scan"
    )
    assert isinstance(scan, pyiconeus.Scan)
    scan = pyiconeus.open_path("./tests/data" + "/2DScan_v2.source.scan")
    assert isinstance(scan, pyiconeus.Scan)


# Bps open
def test_open_bps():
    bps = pyiconeus.open_path("./tests/data" + "/Mouse.bps")
    assert isinstance(bps, pyiconeus.Bps)


def test_open_bps_v2():
    bps = pyiconeus.open_path(
        "./tests/data" + "/4Dscan_11_StimVIS16__60_30_60_8_fus3D.source_v2.bps"
    )
    assert isinstance(bps, pyiconeus.Bps)


# Roi open
def test_open_roi():
    roi = pyiconeus.open_path("./tests/data" + "/roi_for_4DStacked.bri")
    assert isinstance(roi, pyiconeus.Roi)


def test_open_roi_binary():
    roi = pyiconeus.open_path("./tests/data" + "/roiread_binary.bri")
    assert isinstance(roi, pyiconeus.Roi)


def test_open_raw():
    raw = pyiconeus.open_path(
        "./tests/data" + "/2DScan_v2.raw", "./tests/data" + "/2DScan_v2.hraw"
    )
    assert isinstance(raw, pyiconeus.Raw)
