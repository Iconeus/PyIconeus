"""Developer utility: download IcoScan test data from Zenodo for the test suite."""

import hashlib
import os
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

RECORD_ID = "22249523"
FILENAME = "test_data_pyiconeus.zip"
DESTINATION = "tests/data"
LOCAL_PATH = "./test_data_pyiconeus.zip"


def get_zenodo_md5(record_id, filename):
    url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    files = response.json().get("files", [])
    for file_info in files:
        if file_info.get("key") == filename:
            checksum = file_info.get("checksum", "")
            if checksum.startswith("md5:"):
                return checksum.split("md5:")[1]
    return None


def calculate_local_md5(filepath, chunk_size=8192):
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def verify_file(record_id, filepath, filename):

    expected_md5 = get_zenodo_md5(record_id, filename)

    if not expected_md5:
        print(f"Error : Unable to open '{filename}' in record {record_id}.")
        return False

    local_md5 = calculate_local_md5(filepath)

    print(f"MD5 Zenodo : {expected_md5}")
    print(f"MD5 Local  : {local_md5}")

    if local_md5.lower() == expected_md5.lower():
        print("Success")
        return True
    else:
        print("Error : checksums do not match")
        return False


def download_test_data(dest: str, record_id: str, filename: str) -> bool:
    destination = Path(dest)
    if destination.is_dir() and any(destination.iterdir()):
        return False
    print("Downloading test data...")
    url = f"https://zenodo.org/records/{record_id}/files/{filename}"
    print(url)

    response = requests.get(url, stream=True)

    # Sizes in bytes.
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024
    archive = Path(filename)

    with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
        with open(archive, "wb") as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(destination.parent)
    return True


if __name__ == "__main__":
    if download_test_data(DESTINATION, RECORD_ID, FILENAME):
        print("Checksum check...")
        if verify_file(RECORD_ID, LOCAL_PATH, FILENAME):
            os.remove(FILENAME)
    else:
        print("Test data already exists; skipping download and checksum.")
