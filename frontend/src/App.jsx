import { useRef, useState } from "react"; // useRef = handle to the <audio>, useState = UI data

const API = "http://localhost:8000"; // where the backend runs

function fmt(sec) { // turn 125.4 seconds into "2:05"
  const m = Math.floor(sec / 60); // whole minutes
  const s = String(Math.floor(sec % 60)).padStart(2, "0"); // seconds, padded to 2 digits
  return `${m}:${s}`; // combine
}

export default function App() { // the whole UI is one component
  const audioRef = useRef(); // will point at the <audio> element
  const [query, setQuery] = useState(""); // what the user typed
  const [results, setResults] = useState([]); // search results from the backend
  const [status, setStatus] = useState(""); // small message under the header
  const [active, setActive] = useState(null); // which result is currently playing

  async function upload(e) { // runs when a file is chosen
    const file = e.target.files[0]; // the chosen file
    if (!file) return; // nothing chosen, stop
    setStatus(`Transcribing ${file.name}... this can take a minute`); // tell the user to wait
    const form = new FormData(); // multipart body, like an HTML form
    form.append("file", file); // field name must match the backend param "file"
    try { // catch network errors
      const res = await fetch(`${API}/upload`, { method: "POST", body: form }); // send to backend
      const data = await res.json(); // read the reply
      setStatus(`Indexed ${data.chunks} chunks from ${file.name}`); // success message
    } catch { // backend down or request failed
      setStatus("Upload failed. Is the backend running on port 8000?"); // helpful error
    }
  }

  async function search(e) { // runs when the form is submitted
    e.preventDefault(); // stop the page from reloading
    if (!query.trim()) return; // ignore empty searches
    const res = await fetch(`${API}/search?q=${encodeURIComponent(query)}`); // ask the backend
    setResults(await res.json()); // save results to show them
    setActive(null); // clear the old highlight
  }

  function jump(r, i) { // runs when a result is clicked
    const a = audioRef.current; // the <audio> element
    const url = `${API}/${r.file}`; // full URL of the audio file
    const seek = () => { a.currentTime = r.start; a.play(); }; // jump to the timestamp and play
    if (a.src === url) seek(); // same file already loaded: just seek
    else { a.src = url; a.onloadedmetadata = seek; } // new file: load it, then seek once ready
    setActive(i); // highlight this result
  }

  return ( // what gets drawn on screen
    <main> {/* page container */}
      <header> {/* top section */}
        <h1>Find the moment</h1> {/* page title */}
        <p>Search what was said across your recordings, then jump straight to it.</p> {/* one-line explainer */}
        <label className="file"> {/* styled file picker */}
          Add a recording {/* button text */}
          <input type="file" accept="audio/*,video/*" onChange={upload} hidden /> {/* hidden real input */}
        </label>
        <span className="status">{status}</span> {/* progress or error text */}
      </header>

      <form onSubmit={search}> {/* search bar */}
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="the call about payment retries" /> {/* controlled input */}
        <button>Search</button> {/* submit button */}
      </form>

      <audio ref={audioRef} controls /> {/* the single player, controlled via the ref */}

      <ul> {/* results list */}
        {results.map((r, i) => ( // one row per result
          <li key={i} className={i === active ? "on" : ""}> {/* highlight the active one */}
            <button onClick={() => jump(r, i)}> {/* click = seek and play */}
              <span className="time">{fmt(r.start)}</span> {/* timestamp chip */}
              <span className="body"> {/* text column */}
                <strong>{r.name}</strong> {/* original file name */}
                <span>{r.text}</span> {/* matching transcript chunk */}
              </span>
              <span className="score">{Math.round(r.score * 100)}%</span> {/* similarity as a percent */}
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}
