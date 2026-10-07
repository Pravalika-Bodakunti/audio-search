import { defineConfig } from "vite"; // Vite config helper
import react from "@vitejs/plugin-react"; // lets Vite understand JSX
export default defineConfig({ plugins: [react()] }); // enable the React plugin
