# SPDX-FileCopyrightText: 2026-present Iconeus
#
# SPDX-License-Identifier: BSD-3-Clause

"""Test data, fetched per file from a Hugging Face dataset and cached."""

import os

import pytest
from huggingface_hub import hf_hub_download, snapshot_download

REPO = os.environ.get("PYICONEUS_TEST_REPO", "ArthurZ/pyiconeus-test-data")
REVISION = os.environ.get(
    "PYICONEUS_TEST_REVISION", "ed64082ce809843fe11796f0116873f5fb5981df"
)


@pytest.fixture(scope="session")
def data_path():
    """Return a local path for a dataset file, downloading it once if needed."""

    def get(name: str) -> str:
        return hf_hub_download(REPO, name, repo_type="dataset", revision=REVISION)

    return get


if __name__ == "__main__":
    print(snapshot_download(REPO, repo_type="dataset", revision=REVISION))
