// frontend/src/components/ChatPanel.jsx

import { useState, useRef, useEffect } from "react";

import { askQuestion } from "../api/client";
import DualOutput from "./DualOutput";
import VoiceButton from "./VoiceButton";
import DocumentUpload from "./DocumentUpload";
import DocResult from "./DocResult";

const SUGGESTIONS = [
  "What is the punishment for murder under IPC?",
  "What are my rights if I am arrested?",
  "How long can police detain me without a court order?",
  "What is bail and how can I apply for it?",
];

export default function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState([]);
  const [docResult, setDocResult] = useState(null);

  const [loading, setLoading] = useState(false);

  // NEW
  const [threadId, setThreadId] = useState(null);
  const [detectedLang, setDetectedLang] = useState("en");

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [history, loading, docResult]);

  // ─────────────────────────────────────────────────────────────────────
  // Submit
  // ─────────────────────────────────────────────────────────────────────

  async function submit(q) {
    const text = (q || question).trim();

    if (!text || loading) return;

    setQuestion("");
    setLoading(true);

    setHistory((h) => [
      ...h,
      {
        question: text,
        data: null,
        error: null,
      },
    ]);

    try {
      const data = await askQuestion({
        question: text,
        language: "auto",
        thread_id: threadId,
      });

      // Save thread ID
      if (data.thread_id) {
        setThreadId(data.thread_id);
      }

      // Save detected language
      if (data.detected_language) {
        setDetectedLang(data.detected_language);
      }

      setHistory((h) => {
        const updated = [...h];
        updated[updated.length - 1].data = data;
        return updated;
      });
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        "Something went wrong.";

      setHistory((h) => {
        const updated = [...h];
        updated[updated.length - 1].error = msg;
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "18px 24px",
          borderBottom: "1px solid var(--c-border)",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          background: "var(--c-header-bg)",
        }}
      >
        <span style={{ fontSize: "22px" }}>
          ⚖️
        </span>

        <div>
          <div
            style={{
              fontWeight: 700,
              fontSize: "17px",
              color: "var(--c-text)",
            }}
          >
            NyayaSetu
          </div>

          <div
            style={{
              fontSize: "12px",
              color: "var(--c-muted)",
            }}
          >
            AI legal aid · Indian law · IPC · BNS · CrPC
          </div>

          {/* Language indicator */}
          {detectedLang &&
            detectedLang !== "en" && (
              <div
                style={{
                  marginTop: 4,
                  fontSize: 11,
                  padding: "2px 8px",
                  borderRadius: 20,
                  background: "var(--c-tag-bg)",
                  color: "var(--c-tag-text)",
                  display: "inline-block",
                }}
              >
                🌐 {detectedLang.toUpperCase()} detected
              </div>
            )}
        </div>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          gap: "32px",
        }}
      >
        {/* Welcome */}
        {history.length === 0 &&
          !docResult && (
            <div
              style={{
                textAlign: "center",
                marginTop: "60px",
              }}
            >
              <div
                style={{
                  fontSize: "40px",
                  marginBottom: "12px",
                }}
              >
                🏛️
              </div>

              <div
                style={{
                  fontSize: "20px",
                  fontWeight: 600,
                  color: "var(--c-text)",
                  marginBottom: "8px",
                }}
              >
                Ask about your legal rights
              </div>

              <div
                style={{
                  color: "var(--c-muted)",
                  marginBottom: "32px",
                  fontSize: "14px",
                }}
              >
                Covering IPC, BNS, CrPC and Supreme Court judgments
              </div>

              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "10px",
                  justifyContent: "center",
                }}
              >
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => submit(s)}
                    style={{
                      padding: "10px 16px",
                      borderRadius: "20px",
                      border:
                        "1px solid var(--c-border)",
                      background:
                        "var(--c-surface)",
                      color: "var(--c-text)",
                      cursor: "pointer",
                      fontSize: "13px",
                      textAlign: "left",
                      maxWidth: "280px",
                      lineHeight: 1.4,
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

        {/* Document Result */}
        {docResult && (
          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                marginBottom: 16,
              }}
            >
              <div
                style={{
                  padding: "12px 16px",
                  borderRadius:
                    "16px 16px 4px 16px",
                  background:
                    "var(--c-user-bubble)",
                  color: "#fff",
                  fontSize: 14,
                }}
              >
                📄 Uploaded a legal document
              </div>
            </div>

            <DocResult data={docResult} />
          </div>
        )}

        {/* Chat history */}
        {history.map((item, i) => (
          <div key={i}>
            {/* User bubble */}
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                marginBottom: "16px",
              }}
            >
              <div
                style={{
                  maxWidth: "70%",
                  padding: "12px 16px",
                  borderRadius:
                    "16px 16px 4px 16px",
                  background:
                    "var(--c-user-bubble)",
                  color:
                    "var(--c-user-text)",
                  fontSize: "14px",
                  lineHeight: 1.6,
                }}
              >
                {item.question}
              </div>
            </div>

            {/* AI response */}
            {item.data && (
              <DualOutput data={item.data} />
            )}

            {/* Error */}
            {item.error && (
              <div
                style={{
                  padding: "14px 18px",
                  borderRadius: "10px",
                  background:
                    "var(--c-error-bg)",
                  color:
                    "var(--c-error-text)",
                  fontSize: "14px",
                }}
              >
                ⚠️ {item.error}
              </div>
            )}
          </div>
        ))}

        {/* Loading */}
        {loading && (
          <div
            style={{
              display: "flex",
              gap: "6px",
              alignItems: "center",
              color: "var(--c-muted)",
              fontSize: "14px",
            }}
          >
            <span
              style={{
                animation:
                  "pulse 1.2s ease-in-out infinite",
              }}
            >
              ⚖️
            </span>

            <span>
              Retrieving statutes and generating
              response…
            </span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input Bar */}
      <div
        style={{
          padding: "16px 24px",
          borderTop: "1px solid var(--c-border)",
          background: "var(--c-header-bg)",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        <div
          style={{
            display: "flex",
            gap: "10px",
          }}
        >
          <input
            value={question}
            onChange={(e) =>
              setQuestion(e.target.value)
            }
            onKeyDown={(e) =>
              e.key === "Enter" &&
              !e.shiftKey &&
              submit()
            }
            placeholder="Ask about Indian law in plain language…"
            disabled={loading}
            style={{
              flex: 1,
              padding: "12px 16px",
              borderRadius: "10px",
              border:
                "1px solid var(--c-border)",
              background:
                "var(--c-surface)",
              color: "var(--c-text)",
              fontSize: "14px",
              outline: "none",
            }}
          />

          <button
            onClick={() => submit()}
            disabled={
              loading || !question.trim()
            }
            style={{
              padding: "12px 20px",
              borderRadius: "10px",
              border: "none",
              background:
                loading || !question.trim()
                  ? "var(--c-border)"
                  : "#1a6ef5",
              color: "#fff",
              fontWeight: 600,
              fontSize: "14px",
              cursor:
                loading || !question.trim()
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            Ask
          </button>

          <VoiceButton
            onResult={({ question: q, data }) => {
              setHistory((h) => [
                ...h,
                {
                  question: q,
                  data,
                  error: null,
                },
              ]);
            }}
          />

          <DocumentUpload
            onResult={(data) => {
              setDocResult(data);

              bottomRef.current?.scrollIntoView({
                behavior: "smooth",
              });
            }}
          />
        </div>
      </div>
    </div>
  );
}