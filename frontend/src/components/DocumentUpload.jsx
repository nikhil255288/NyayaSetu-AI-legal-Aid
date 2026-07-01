// frontend/src/components/DocumentUpload.jsx
import { useState, useRef } from "react";

export default function DocumentUpload({ onResult }) {
  const [state, setState] = useState("idle"); // idle | uploading | done | error
  const [error, setError] = useState("");
  const fileRef = useRef(null);

  async function handleFile(file) {
    if (!file) return;
    setState("uploading");
    setError("");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }
      const data = await res.json();
      setState("done");
      onResult(data);
    } catch (e) {
      setError(e.message);
      setState("error");
    }
  }

  return (
    <div>
      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.txt,.png,.jpg,.jpeg"
        style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files[0])}
      />
      <button
        onClick={() => fileRef.current?.click()}
        disabled={state === "uploading"}
        style={{
          padding: "12px 18px",
          borderRadius: "10px",
          border: "1px solid var(--c-border)",
          background: "var(--c-surface)",
          color: "var(--c-text)",
          fontWeight: 600,
          fontSize: "13px",
          cursor: state === "uploading" ? "not-allowed" : "pointer",
          whiteSpace: "nowrap",
        }}
      >
        {state === "uploading" ? "⏳ Reading doc…" : "📄 Upload FIR / Bail / Summons"}
      </button>
      {error && (
        <div style={{ marginTop: 6, fontSize: 12, color: "var(--c-error-text)" }}>
          {error}
        </div>
      )}
    </div>
  );
}