import os  # for changing the working folder
import sys  # to make main.py importable
from pathlib import Path  # nicer file paths
import pytest  # test framework

BACKEND = Path(__file__).resolve().parent.parent  # the backend/ folder
FIXTURES = Path(__file__).resolve().parent / "fixtures"  # sample audio used by the tests
sys.path.insert(0, str(BACKEND))  # so "import main" finds backend/main.py


@pytest.fixture(scope="session")  # one setup shared by every test (models load only once)
def main(tmp_path_factory):  # gives tests the imported main module
    work = tmp_path_factory.mktemp("work")  # empty temp folder for this test run
    os.chdir(work)  # main.py creates uploads/ and chroma_db/ in the current folder, so keep them out of the real ones
    import main as app_module  # importing loads Whisper + the embedder (slow the first time)
    return app_module  # hand the module to the tests


@pytest.fixture(scope="session")  # one client for the whole run
def client(main):  # an HTTP client that talks to the app without starting a server
    from fastapi.testclient import TestClient  # FastAPI's built-in test client
    return TestClient(main.app)  # wrap our app


@pytest.fixture(scope="session")  # upload the sample recordings once
def indexed(client):  # returns the upload responses keyed by file name
    out = {}  # name -> JSON reply
    for name in ["payments.wav", "holiday.wav"]:  # two recordings on different topics
        with open(FIXTURES / name, "rb") as f:  # open the sample file
            r = client.post("/upload", files={"file": (name, f, "audio/wav")})  # send it like the browser does
        assert r.status_code == 200, r.text  # upload must succeed
        out[name] = r.json()  # remember the reply
    return out  # e.g. {"payments.wav": {"id": "...", "chunks": 1}, ...}
