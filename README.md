# PyIconeus

[![PyPI - Version](https://img.shields.io/pypi/v/pyiconeus.svg)](https://pypi.org/project/pyiconeus)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyiconeus.svg)](https://pypi.org/project/pyiconeus)
[![PyPI - Numpy Version](https://img.shields.io/pypi/pyversions/numpy.svg)](https://pypi.org/project/numpy)

**PyIconeus** is the official IO python package from Iconeus. Its purpose is to give an easy to use, open-source library for reading and using the Iconeus official formats.
PyIconeus handles the following file formats:
  - .scan
  - .bps
  - .bri
  - .raw with .hraw

-----

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

1. Setting up a virtual enironment

The use of a python virtual environment is recommended to avoid conflicts with other Python packages.

You can create a virtual environment using uv:

```console
uv venv
.venv/Script/activate
```

3. Install PyIconeus

With Uv:
```console
uv add pyiconeus
```

With pip:

```console
uv pip install pyiconeus
```

Or with the sources:
```console
uv pip install -e .
```

4. Check installation

Run the tests to see if they all passes

```console
pytest
```

## Usage

Examples scripts can be found in './examples' to understand how to use the library

## License

`pyiconeus` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
