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
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
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

  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const providers = [
    { value: "gemini", label: "Gemini", color: "#DF7F83" },
    { value: "groq", label: "Groq", color: "#464646" },
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
        <div style={{ position: "relative" }} ref={dropdownRef}>
          <button
            type="button"
            className={styles.modelPill}
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          >
            <svg width="14" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span>{currentProvider?.label}</span>
            <svg 
              width="10" height="6" viewBox="0 0 10 6" fill="none" 
              style={{ transform: isDropdownOpen ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s" }}
            >
              <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          {isDropdownOpen && (
            <div className={styles.dropdown}>
              {providers.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => handleSelectProvider(p.value)}
                  className={`${styles.dropdownItem} ${provider === p.value ? styles.dropdownItemActive : ""}`}
                >
                  <div className={styles.dropdownItemSelector} style={{ background: provider === p.value ? 'white' : p.color }}></div>
                  {p.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <textarea
          ref={textareaRef}
          className={styles.textarea}
          rows={1}
          placeholder="Ask DocMind anything..."
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />

        <button
          type="submit"
          className={styles.sendBtn}
          disabled={disabled || !text.trim()}
          title="Send message"
        >
          <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>
      </form>
    </div>
  );
}
