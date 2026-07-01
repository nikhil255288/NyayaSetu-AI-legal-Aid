// frontend/src/components/DualOutput.jsx
import CitationCard from "./CitationCard";

export default function DualOutput({ data }) {
  if (!data) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

      {/* Plain language — shown first, most prominent */}
      <div style={{
        padding: "20px",
        borderRadius: "12px",
        background: "var(--c-plain-bg)",
        border: "1px solid var(--c-plain-border)",
      }}>
        <div style={{
          fontSize: "11px",
          fontWeight: 700,
          letterSpacing: "0.08em",
          color: "var(--c-plain-label)",
          marginBottom: "10px",
          textTransform: "uppercase",
        }}>
          🟢 Plain language answer
        </div>

        <p style={{
          margin: 0,
          lineHeight: 1.75,
          color: "var(--c-text)",
          fontSize: "15px",
          whiteSpace: "pre-wrap",
        }}>
          {data.plain_response}
        </p>
      </div>

      {/* Legal cited response */}
      <div style={{
        padding: "20px",
        borderRadius: "12px",
        background: "var(--c-legal-bg)",
        border: "1px solid var(--c-legal-border)",
      }}>
        <div style={{
          fontSize: "11px",
          fontWeight: 700,
          letterSpacing: "0.08em",
          color: "var(--c-legal-label)",
          marginBottom: "10px",
          textTransform: "uppercase",
        }}>
          ⚖️ Legal response with citations
        </div>

        <p style={{
          margin: 0,
          lineHeight: 1.75,
          color: "var(--c-text)",
          fontSize: "14px",
          fontFamily: "Georgia, serif",
          whiteSpace: "pre-wrap",
        }}>
          {data.legal_response}
        </p>
      </div>

      <CitationCard
        citations={data.citations}
        sources={data.sources}
        iterations={data.iterations}
      />

      {/* Escalation banner — shown when AI hands off to human */}
      {data.escalated && (
        <div style={{
          padding: "16px 20px",
          borderRadius: "12px",
          background: "var(--c-error-bg)",
          border: "1px solid var(--c-error-text)",
          display: "flex",
          gap: "12px",
          alignItems: "flex-start",
        }}>
          <span style={{ fontSize: "20px" }}>🚨</span>

          <div>
            <div style={{
              fontWeight: 700,
              color: "var(--c-error-text)",
              marginBottom: "4px",
              fontSize: "13px",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}>
              Referred to human legal aid
            </div>

            <div style={{
              fontSize: "13px",
              color: "var(--c-text)",
              lineHeight: 1.6,
            }}>
              {data.escalation_reason || "This case needs a qualified lawyer."}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}