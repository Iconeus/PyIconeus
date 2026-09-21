# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

"""Test data access, backed by a Hugging Face bucket.

Replaces download_script.py: fixtures are fetched per file, on first use, and
cached across runs, instead of downloading the full 3.2 GB archive up front.

Override the source with PYICONEUS_TEST_BUCKET (e.g. once the bucket is
transferred to an Iconeus namespace) or the cache location with
PYICONEUS_TEST_DATA.
"""

import os
from pathlib import Path

import pytest
from huggingface_hub import download_bucket_files

BUCKET = os.environ.get("PYICONEUS_TEST_BUCKET", "ArthurZ/pyiconeus-test-data")
CACHE = Path(
    os.environ.get(
        "PYICONEUS_TEST_DATA", Path.home() / ".cache" / "pyiconeus-test-data"
    )
)


@pytest.fixture(scope="session")
def data_path():
    """Return a local path for a bucket file, downloading it once if needed."""

    def get(name: str) -> str:
        local = CACHE / name
        if not local.exists():
            local.parent.mkdir(parents=True, exist_ok=True)
            download_bucket_files(BUCKET, [(name, local)])
        return str(local)

    return get
