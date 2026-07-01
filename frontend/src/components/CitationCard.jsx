// frontend/src/components/CitationCard.jsx
export default function CitationCard({ citations, iterations }) {
    if (!citations?.length) return null;
    return (
      <div style={{
        marginTop: "12px",
        padding: "12px 16px",
        borderRadius: "10px",
        background: "var(--c-surface)",
        border: "1px solid var(--c-border)",
        fontSize: "13px",
      }}>
        <div style={{ fontWeight: 600, marginBottom: "8px", color: "var(--c-muted)" }}>
          📎 Citations · {iterations} retrieval round{iterations !== 1 ? "s" : ""}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
          {citations.map((c) => (
            <span key={c.ref} style={{
              padding: "3px 10px",
              borderRadius: "20px",
              background: "var(--c-tag-bg)",
              color: "var(--c-tag-text)",
              fontFamily: "monospace",
              fontSize: "12px",
            }}>
              {c.ref}
            </span>
          ))}
        </div>
      </div>
    );
  }