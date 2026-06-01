import { useRef, useState, useEffect } from "react";
import styles from "./ChatInput.module.css";

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState("");
  const [provider, setProvider] = useState("gemini");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const textareaRef = useRef(null);
  const dropdownRef = useRef(null);

  function handleInput(e) {
    setText(e.target.value);
    const ta = textareaRef.current;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const q = text.trim();
    if (!q || disabled) return;
    onSend(q, provider);
    setText("");
    const ta = textareaRef.current;
    if (ta) ta.style.height = "auto";
  }

  function handleSelectProvider(value) {
    setProvider(value);
    setIsDropdownOpen(false);
  }

  function handleClickOutside(e) {
    if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
      setIsDropdownOpen(false);
    }
  }

  useEffect(() => {
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const providers = [
    { value: "gemini", label: "Gemini" },
    { value: "groq", label: "Groq" },
  ];

  const currentProvider = providers.find((p) => p.value === provider);

  return (
    <div className={styles.dock}>
      <form
        className={styles.row}
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        {/* Dropup */}
        <div
          className={styles.modelPill}
          ref={dropdownRef}
          style={{ position: "relative" }}
        >
          <button
            type="button"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "inherit",
              fontSize: "inherit",
              padding: "0",
            }}
          >
            <svg
              width="14"
              height="14"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              style={{ color: "var(--rose)", flexShrink: 0 }}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            <span>{currentProvider?.label}</span>
            <svg
              width="10"
              height="6"
              viewBox="0 0 10 6"
              fill="none"
              style={{
                flexShrink: 0,
                pointerEvents: "none",
                // Arrow points UP when open (it's a dropup), DOWN when closed
                transform: isDropdownOpen ? "rotate(0deg)" : "rotate(180deg)",
                transition: "transform 0.2s",
              }}
            >
              <path
                d="M1 5l4-4 4 4"
                stroke="#DF7F83"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>

          {/* Dropup menu — anchored ABOVE the button via bottom: 100% */}
          {isDropdownOpen && (
            <div
              style={{
                position: "absolute", // relative to modelPill, not the viewport
                bottom: "calc(100% + 8px)", // 8px gap above the button
                left: "0",
                backgroundColor: "#1a1a1a",
                border: "1px solid #333",
                borderRadius: "8px",
                boxShadow: "0 -4px 12px rgba(0,0,0,0.3)",
                zIndex: 100,
                minWidth: "105px",
                overflow: "hidden",
              }}
            >
              {providers.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => handleSelectProvider(p.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    textAlign: "left",
                    background:
                      provider === p.value ? "#DF7F83" : "transparent",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "14px",
                    color: provider === p.value ? "#fff" : "#ccc",
                    transition: "background 0.15s",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                  onMouseEnter={(e) => {
                    if (provider !== p.value) {
                      e.currentTarget.style.background =
                        "rgba(212, 181, 182, 0.2)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (provider !== p.value) {
                      e.currentTarget.style.background = "transparent";
                    }
                  }}
                >
                  
                  <span>{p.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          rows={1}
          placeholder="Ask about your documents…"
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />

        {/* Send button */}
        <button
          type="submit"
          className={styles.sendBtn}
          disabled={disabled || !text.trim()}
        >
          <span className={styles.sendLabel}>Send</span>
          <svg
            width="13"
            height="13"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M14 5l7 7m0 0l-7 7m7-7H3"
            />
          </svg>
        </button>
      </form>
    </div>
  );
}
