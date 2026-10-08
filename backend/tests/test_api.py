import io  # in-memory files
import wave  # to build a silent WAV on the fly
from pathlib import Path  # nicer file paths

FIXTURES = Path(__file__).resolve().parent / "fixtures"  # sample audio folder


def test_upload_transcribes_and_indexes(indexed):  # both samples produce searchable chunks
    for name, reply in indexed.items():  # each uploaded recording
        assert reply["chunks"] >= 1, name  # at least one chunk was stored
        assert len(reply["id"]) == 8  # short unique id


def test_search_finds_the_right_recording(client, indexed):  # the core feature: search by meaning
    r = client.get("/search", params={"q": "that call about failed card charges"})  # no exact words from the audio
    top = r.json()[0]  # best match
    assert top["name"] == "payments.wav"  # found the payments call
    assert "retr" in top["text"].lower()  # transcript mentions retries
    assert top["start"] == 0.0  # jump-to time for the only chunk


def test_search_ranks_other_topic_lower(client, indexed):  # unrelated recording scores lower
    res = client.get("/search", params={"q": "birthday cake and party music"}).json()  # holiday topic
    assert res[0]["name"] == "holiday.wav"  # right file first
    assert res[0]["score"] > res[1]["score"]  # and ranked above the payments call


def test_search_result_shape(client, indexed):  # the frontend relies on these fields
    res = client.get("/search", params={"q": "restaurant"}).json()  # any query
    assert set(res[0]) >= {"text", "score", "start", "name", "file"}  # all fields present
    assert -1.0 <= res[0]["score"] <= 1.0  # cosine similarity range


def test_search_respects_k(client, indexed):  # k limits the number of results
    assert len(client.get("/search", params={"q": "meeting", "k": 1}).json()) == 1  # only one back


def test_search_requires_query(client):  # q is mandatory
    assert client.get("/search").status_code == 422  # FastAPI validation error


def test_uploaded_audio_is_served(client, indexed):  # the player streams from /uploads
    path = client.get("/search", params={"q": "payment retries"}).json()[0]["file"]  # e.g. uploads/ab12cd34_payments.wav
    r = client.get(f"/{path}")  # what the <audio> element requests
    assert r.status_code == 200  # file is reachable
    assert r.content == (FIXTURES / "payments.wav").read_bytes()  # and unchanged


def test_upload_strips_folder_from_filename(client, main):  # no writing outside uploads/
    buf = io.BytesIO((FIXTURES / "holiday.wav").read_bytes())  # any valid audio
    r = client.post("/upload", files={"file": ("../../evil.wav", buf, "audio/wav")})  # sneaky name
    assert r.status_code == 200  # still accepted
    res = client.get("/search", params={"q": "holiday party", "k": 10}).json()  # find what was stored
    assert all(x["file"].startswith("uploads/") and ".." not in x["file"] for x in res)  # stayed in uploads/


def test_silent_audio_indexes_nothing(client):  # no speech -> zero chunks, no crash
    buf = io.BytesIO()  # build a 2-second silent WAV in memory
    with wave.open(buf, "wb") as w:  # standard WAV writer
        w.setnchannels(1)  # mono
        w.setsampwidth(2)  # 16-bit
        w.setframerate(16000)  # 16 kHz
        w.writeframes(b"\x00\x00" * 32000)  # all zeros = silence
    buf.seek(0)  # rewind before sending
    r = client.post("/upload", files={"file": ("silence.wav", buf, "audio/wav")})  # upload it
    assert r.status_code == 200  # handled gracefully
    assert r.json()["chunks"] == 0  # nothing to index
