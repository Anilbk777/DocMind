import { useRef, useState } from 'react';
import styles from './ChatInput.module.css';

export default function ChatInput({ onSend, disabled }) {
  const [text,     setText]     = useState('');
  const [provider, setProvider] = useState('gemini');
  const textareaRef = useRef(null);

  function handleInput(e) {
    setText(e.target.value);
    const ta = textareaRef.current;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const q = text.trim();
    if (!q || disabled) return;
    onSend(q, provider);
    setText('');
    const ta = textareaRef.current;
    if (ta) { ta.style.height = 'auto'; }
  }

  return (
    <div className={styles.dock}>
      <form className={styles.row} onSubmit={e => { e.preventDefault(); submit(); }}>
        {/* Model selector */}
        <div className={styles.modelPill}>
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: 'var(--rose)', flexShrink: 0 }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
          <select value={provider} onChange={e => setProvider(e.target.value)} className={styles.select}>
            <option value="gemini">Gemini</option>
            <option value="groq">Groq</option>
          </select>
          <svg width="10" height="6" viewBox="0 0 10 6" fill="none" style={{ flexShrink: 0, pointerEvents: 'none' }}>
            <path d="M1 1l4 4 4-4" stroke="#DF7F83" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
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

        {/* Send */}
        <button type="submit" className={styles.sendBtn} disabled={disabled || !text.trim()}>
          Send
          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
          </svg>
        </button>
      </form>
      <p className={styles.hint}>Shift+Enter for new line · Enter to send</p>
    </div>
  );
}
