# PyIconeus

[![NumPy](https://img.shields.io/badge/NumPy-4DABCF?logo=numpy&logoColor=fff)]()
[![Pytest](https://img.shields.io/badge/Pytest-fff?logo=pytest&logoColor=000)](#)
[![PyIconeus](https://github.com/Iconeus/PyIconeus/actions/workflows/python-package.yml/badge.svg?branch=main)](https://github.com/Iconeus/PyIconeus/actions/workflows/python-package.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21807850.svg)](https://doi.org/10.5281/zenodo.21807850)

**PyIconeus** is Iconeus' open-source Python library for reading Iconeus data
formats. It exposes the `Scan`, `Bps`, `Roi` and `Raw` models through a single
file-opening entry point.

Supported formats:

- `.scan` (legacy HDF5 and binary scan files)
- `.bps` (HDF5 and binary Brain-to-Lab transforms)
- `.bri` (HDF5 and binary ROI meshes)
- `.raw` with its associated `.hraw` header (IQ data)

-----

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

1. Set up a virtual environment

The use of a python virtual environment is recommended to avoid conflicts with other Python packages.

You can create a virtual environment using uv:

```console
uv venv
   .venv/Scripts/activate       # Windows
   source .venv/bin/activate    # Linux/macOS
```

2. Install PyIconeus

With Uv:
```console
uv pip install pyiconeus
```

With pip:

```console
python -m pip install pyiconeus
```

Or with the sources:
```console
python -m pip install -e .
```

3. Check the installation

Run the tests (the repository test data must be present):

```console
pytest
```

## Usage

```python
from pyiconeus import open_path

scan = open_path("acquisition.scan")
bps = open_path("positioning.bps")
scan.bps = bps

# RAW data requires both files. blockStart and blockEnd are one-based and
# inclusive; their defaults load the first block only.
raw = open_path("acquisition.raw", "acquisition.hraw", blockStart=1, blockEnd=1)
```

See the [documentation](https://iconeus.github.io/PyIconeus/) and the
[`examples`](./examples) notebooks for more complete examples.

`open_path` determines the model from the lowercase filename extension. It
raises `FileNotFoundError` for missing paths, `ValueError` for unsupported
extensions or invalid RAW arguments, and may raise `OSError` when a file is
not readable or has invalid content.

## Requirements

Python 3.10 or newer is supported. Runtime dependencies are NumPy, pytz, h5py
and transforms3d. Test dependencies are available with:

```console
python -m pip install -e ".[dependencies]"
```

## License

`pyiconeus` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
