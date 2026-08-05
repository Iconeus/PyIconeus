import urllib.request, zipfile, os

ZENODO_URL = "https://zenodo.org/records/21807850/files/data.zip"

def download_test_data(dest="tests/data"):
    if os.path.exists(dest):
        return
    print("Downloading test data...")
    urllib.request.urlretrieve(ZENODO_URL, "data.zip")
    with zipfile.ZipFile("data.zip") as z:
        z.extractall("tests")
    os.remove("data.zip")

if __name__ == '__main__':
    download_test_data()
