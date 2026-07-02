// frontend/src/api/client.js
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export async function askQuestion({ question, language = "en", thread_id = null }) {
  const payload = { question, language };
  if (thread_id) payload.thread_id = thread_id;

  const { data } = await api.post("/query", payload);
  return data;
}