import React from "react"; // React core
import { createRoot } from "react-dom/client"; // mounts React into the page
import App from "./App.jsx"; // our main component
import "./App.css"; // global styles
createRoot(document.getElementById("root")).render(<App />); // draw <App /> inside <div id="root">
