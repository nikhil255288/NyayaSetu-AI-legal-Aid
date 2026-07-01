// frontend/src/App.jsx
import ChatPanel from "./components/ChatPanel";

export default function App() {
  return (
    <>
      <style>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

        :root {
          --c-bg:            #f7f7f5;
          --c-surface:       #ffffff;
          --c-header-bg:     #ffffff;
          --c-border:        #e4e4e0;
          --c-text:          #1a1a18;
          --c-muted:         #6b6b67;
          --c-user-bubble:   #1a6ef5;
          --c-user-text:     #ffffff;
          --c-plain-bg:      #eaf3de;
          --c-plain-border:  #b6d98a;
          --c-plain-label:   #3b6d11;
          --c-legal-bg:      #eef3fb;
          --c-legal-border:  #b5cff4;
          --c-legal-label:   #185fa5;
          --c-tag-bg:        #ede9fd;
          --c-tag-text:      #3c3489;
          --c-error-bg:      #fdf2f2;
          --c-error-text:    #a32d2d;
        }

        @media (prefers-color-scheme: dark) {
          :root {
            --c-bg:            #1a1a18;
            --c-surface:       #252522;
            --c-header-bg:     #1f1f1d;
            --c-border:        #3a3a36;
            --c-text:          #e8e8e0;
            --c-muted:         #888880;
            --c-user-bubble:   #1a6ef5;
            --c-user-text:     #ffffff;
            --c-plain-bg:      #1a2e10;
            --c-plain-border:  #3b6d11;
            --c-plain-label:   #97c459;
            --c-legal-bg:      #0d1e36;
            --c-legal-border:  #185fa5;
            --c-legal-label:   #85b7eb;
            --c-tag-bg:        #26215c;
            --c-tag-text:      #afa9ec;
            --c-error-bg:      #2a1010;
            --c-error-text:    #f09595;
          }
        }

        body { background: var(--c-bg); color: var(--c-text); }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
      <ChatPanel />
    </>
  );
}