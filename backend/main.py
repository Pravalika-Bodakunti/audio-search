import os  # for folders and file paths
import uuid  # to give every upload a unique id
from fastapi import FastAPI, UploadFile  # FastAPI = web framework, UploadFile = uploaded file type
from fastapi.middleware.cors import CORSMiddleware  # lets the browser frontend call this API
from fastapi.staticfiles import StaticFiles  # serves audio files so the player can stream them
from faster_whisper import WhisperModel  # speech-to-text (runs locally, free)
from sentence_transformers import SentenceTransformer  # turns text into vectors (embeddings)
import chromadb  # local vector database

os.makedirs("uploads", exist_ok=True)  # create the uploads folder if it doesn't exist

whisper = WhisperModel("base", compute_type="int8")  # "base" = small and fast; int8 = runs well on CPU
embedder = SentenceTransformer("all-MiniLM-L6-v2")  # small, free embedding model
db = chromadb.PersistentClient(path="./chroma_db")  # saves vectors to disk so they survive restarts
col = db.get_or_create_collection("audio", metadata={"hnsw:space": "cosine"})  # cosine similarity search

app = FastAPI()  # create the app
app.add_middleware(  # allow the React dev server to call us
    CORSMiddleware,  # the CORS handler
    allow_origins=["http://localhost:5173"],  # only our frontend address
    allow_methods=["*"],  # allow GET, POST, etc.
    allow_headers=["*"],  # allow any request headers
)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")  # audio available at /uploads/<file>


def chunk(segments, window=30):  # group short Whisper segments into ~30 second chunks
    out, buf, t0 = [], [], None  # out = results, buf = texts collected so far, t0 = chunk start time
    for s in segments:  # each segment has .start, .end (seconds) and .text
        if t0 is None:  # first segment of a new chunk
            t0 = s.start  # remember when this chunk starts: this is our "jump to" time
        buf.append(s.text.strip())  # add this segment's text to the chunk
        if s.end - t0 >= window:  # chunk is long enough
            out.append((t0, " ".join(buf)))  # save (start_time, full_text)
            buf, t0 = [], None  # reset for the next chunk
    if buf:  # leftover text at the end
        out.append((t0, " ".join(buf)))  # save the final chunk
    return out  # list of (start_time, text)


@app.post("/upload")  # endpoint: POST /upload
def upload(file: UploadFile):  # plain "def" so FastAPI runs the slow work in a thread
    fid = str(uuid.uuid4())[:8]  # short unique id
    name = os.path.basename(file.filename)  # strip any folder parts for safety
    path = f"uploads/{fid}_{name}"  # where we store the audio
    with open(path, "wb") as f:  # open the destination file for writing
        f.write(file.file.read())  # copy the uploaded bytes to disk
    segs, _ = whisper.transcribe(path, vad_filter=True)  # transcribe; vad_filter skips silence
    chunks = chunk(list(segs))  # turn the segment stream into timed chunks
    if not chunks:  # nothing was recognised
        return {"id": fid, "chunks": 0}  # return early
    texts = [c[1] for c in chunks]  # just the text of each chunk
    col.add(  # store everything in Chroma
        ids=[f"{fid}-{i}" for i in range(len(chunks))],  # unique id per chunk
        documents=texts,  # the readable text
        embeddings=embedder.encode(texts).tolist(),  # the vector for each chunk
        metadatas=[{"file": path, "name": name, "start": c[0]} for c in chunks],  # file + start time
    )
    return {"id": fid, "chunks": len(chunks)}  # tell the frontend it worked


@app.get("/search")  # endpoint: GET /search?q=...
def search(q: str, k: int = 5):  # q = the query, k = how many results
    vec = embedder.encode([q]).tolist()  # embed the query the same way as the chunks
    r = col.query(query_embeddings=vec, n_results=k)  # find the k closest chunks
    return [  # build a clean list for the frontend
        {"text": d, "score": round(1 - dist, 3), **m}  # text + similarity + file/name/start
        for d, dist, m in zip(r["documents"][0], r["distances"][0], r["metadatas"][0])  # walk the 3 lists together
    ]
