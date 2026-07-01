// frontend/src/components/DocResult.jsx
export default function DocResult({ data }) {
    if (!data) return null;
  
    const DOC_LABELS = {
      FIR: "📋 First Information Report",
      bail_order: "⚖️ Bail Order",
      summons: "📨 Summons",
      chargesheet: "📁 Chargesheet",
      unknown: "📄 Legal Document",
    };
  
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
  
        {/* Header */}
        <div style={{
          padding: "14px 18px",
          borderRadius: "10px",
          background: "var(--c-surface)",
          border: "1px solid var(--c-border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          <div style={{ fontWeight: 700, fontSize: "15px" }}>
            {DOC_LABELS[data.doc_type] || DOC_LABELS.unknown}
          </div>
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {data.sections_cited.slice(0, 5).map((s) => (
              <span key={s} style={{
                padding: "2px 8px",
                borderRadius: "20px",
                background: "var(--c-tag-bg)",
                color: "var(--c-tag-text)",
                fontSize: "11px",
                fontFamily: "monospace",
              }}>{s}</span>
            ))}
          </div>
        </div>
  
        {/* Key facts */}
        {data.key_facts?.length > 0 && (
          <div style={{
            padding: "16px 20px",
            borderRadius: "10px",
            background: "var(--c-surface)",
            border: "1px solid var(--c-border)",
          }}>
            <div style={{ fontWeight: 600, marginBottom: 10, fontSize: 13, color: "var(--c-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Key facts
            </div>
            {data.key_facts.map((f, i) => (
              <div key={i} style={{ fontSize: 14, lineHeight: 1.7, color: "var(--c-text)", paddingLeft: 12, borderLeft: "2px solid var(--c-border)", marginBottom: 6 }}>
                {f}
              </div>
            ))}
          </div>
        )}
  
        {/* Plain explanation */}
        <div style={{
          padding: "18px 20px",
          borderRadius: "10px",
          background: "var(--c-plain-bg)",
          border: "1px solid var(--c-plain-border)",
        }}>
          <div style={{ fontWeight: 700, fontSize: 11, color: "var(--c-plain-label)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            🟢 What this means for you
          </div>
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.75, color: "var(--c-text)", whiteSpace: "pre-wrap" }}>
            {data.plain_explanation}
          </p>
        </div>
  
        {/* Legal response */}
        <div style={{
          padding: "18px 20px",
          borderRadius: "10px",
          background: "var(--c-legal-bg)",
          border: "1px solid var(--c-legal-border)",
        }}>
          <div style={{ fontWeight: 700, fontSize: 11, color: "var(--c-legal-label)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            ⚖️ Legal reading
          </div>
          <p style={{ margin: 0, fontSize: 13, lineHeight: 1.75, color: "var(--c-text)", fontFamily: "Georgia, serif", whiteSpace: "pre-wrap" }}>
            {data.legal_response}
          </p>
        </div>
  
        {/* Urgent actions */}
        {data.urgent_actions?.length > 0 && (
          <div style={{
            padding: "16px 20px",
            borderRadius: "10px",
            background: "var(--c-error-bg)",
            border: "1px solid var(--c-error-text)",
          }}>
            <div style={{ fontWeight: 700, fontSize: 11, color: "var(--c-error-text)", marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              🚨 What to do now
            </div>
            {data.urgent_actions.map((a, i) => (
              <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8, fontSize: 13, color: "var(--c-text)", lineHeight: 1.6 }}>
                <span style={{ fontWeight: 700, color: "var(--c-error-text)", minWidth: 20 }}>{i + 1}.</span>
                <span>{a}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }