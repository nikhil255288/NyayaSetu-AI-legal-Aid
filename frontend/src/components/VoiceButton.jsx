// frontend/src/components/VoiceButton.jsx
import { useState, useRef } from "react";

const STATE = {
  IDLE: "idle",
  RECORDING: "recording",
  PROCESSING: "processing",
  PLAYING: "playing",
};

const LABELS = {
  [STATE.IDLE]: "🎤 Ask by voice",
  [STATE.RECORDING]: "⏹ Stop recording",
  [STATE.PROCESSING]: "⏳ Processing…",
  [STATE.PLAYING]: "🔊 Playing answer…",
};

export default function VoiceButton({ onResult }) {
  const [state, setState] = useState(STATE.IDLE);
  const [error, setError] = useState("");
  const mediaRecorder = useRef(null);
  const chunks = useRef([]);
  const audioRef = useRef(null);

  async function startRecording() {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks.current = [];
      mediaRecorder.current = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });
      mediaRecorder.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data);
      };
      mediaRecorder.current.onstop = handleStop;
      mediaRecorder.current.start();
      setState(STATE.RECORDING);
    } catch {
      setError("Microphone access denied. Please allow mic access and try again.");
    }
  }

  function stopRecording() {
    mediaRecorder.current?.stop();
    mediaRecorder.current?.stream.getTracks().forEach((t) => t.stop());
    setState(STATE.PROCESSING);
  }

  async function handleStop() {
    const blob = new Blob(chunks.current, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("audio", blob, "recording.webm");
    formData.append("language", "en");

    try {
      const res = await fetch("http://localhost:8000/api/voice", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Voice request failed");
      }

      const data = await res.json();

      // Play audio response if available
      if (data.audio_b64) {
        const audioSrc = `data:audio/mp3;base64,${data.audio_b64}`;
        audioRef.current = new Audio(audioSrc);
        setState(STATE.PLAYING);
        audioRef.current.onended = () => setState(STATE.IDLE);
        audioRef.current.play();
      } else {
        setState(STATE.IDLE);
      }

      // Pass result up to ChatPanel
      onResult({
        question: data.transcription,
        data: {
          legal_response: data.legal_response,
          plain_response: data.plain_response,
          citations: data.citations.map((ref) => ({ ref })),
          iterations: 1,
          sources: data.citations,
          escalated: data.escalated,
          escalation_reason: data.escalation_reason,
        },
      });
    } catch (e) {
      setError(e.message || "Something went wrong with voice processing.");
      setState(STATE.IDLE);
    }
  }

  function handleClick() {
    if (state === STATE.IDLE) startRecording();
    else if (state === STATE.RECORDING) stopRecording();
    else if (state === STATE.PLAYING) {
      audioRef.current?.pause();
      setState(STATE.IDLE);
    }
  }

  const isActive = state === STATE.RECORDING || state === STATE.PLAYING;

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={state === STATE.PROCESSING}
        style={{
          padding: "12px 18px",
          borderRadius: "10px",
          border: `2px solid ${isActive ? "#e24b4a" : "var(--c-border)"}`,
          background: isActive ? "#fdf2f2" : "var(--c-surface)",
          color: isActive ? "#a32d2d" : "var(--c-text)",
          fontWeight: 600,
          fontSize: "13px",
          cursor: state === STATE.PROCESSING ? "not-allowed" : "pointer",
          transition: "all 0.2s",
          whiteSpace: "nowrap",
        }}
      >
        {LABELS[state]}
      </button>
      {error && (
        <div style={{
          marginTop: "6px",
          fontSize: "12px",
          color: "var(--c-error-text)",
          maxWidth: "220px",
        }}>
          {error}
        </div>
      )}
    </div>
  );
}