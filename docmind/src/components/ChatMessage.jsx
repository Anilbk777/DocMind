import { useState } from 'react';
import { marked } from 'marked';
import styles from './ChatMessage.module.css';

marked.setOptions({ breaks: true, gfm: true });

function Sources({ sources }) {
  const [open, setOpen] = useState(true);
  if (!sources?.length) return null;
  return (
    <div className={styles.sourcesBlock}>
      <button className={`${styles.sourcesToggle} ${open ? styles.open : ''}`} onClick={() => setOpen(o => !o)}>
        <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/>
        </svg>
        Sources ({sources.length})
      </button>
      {open && (
        <div className={styles.sourcesList}>
          {sources.map((src, i) => (
            <div key={i} className={styles.chip}>
              <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: 'var(--rose)', flexShrink: 0 }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              {src}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ChatMessage({ message }) {
  const { role, body, sources, streaming } = message;
  const isAI = role === 'ai';

  const html = isAI ? marked.parse(body || '') : null;

  if (!isAI) {
    return (
      <div className={`${styles.rowUser} fadein`}>
        <div className={styles.bubbleUser}>{body}</div>
        <div className={`${styles.avatar} ${styles.avatarUser}`}>U</div>
      </div>
    );
  }

  return (
    <div className={`${styles.rowAI} fadein`}>
      <div className={`${styles.avatar} ${styles.avatarAI}`}>DM</div>
      <div className={styles.bubbleAI}>
        <div
          className={`md-body ${streaming ? 'cursor-blink' : ''}`}
          dangerouslySetInnerHTML={{ __html: html }}
        />
        <Sources sources={sources} />
      </div>
    </div>
  );
}
