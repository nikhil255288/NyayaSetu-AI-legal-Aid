// frontend/src/api/client.js
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export async function askQuestion(question) {
  const { data } = await api.post("/query", {
    question,
    language: "en",
  });

  return data;
}