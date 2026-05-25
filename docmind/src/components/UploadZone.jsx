import { useRef } from 'react';
import styles from './UploadZone.module.css';

export default function UploadZone({ onFile }) {
  const inputRef = useRef(null);

  function handleChange(e) {
    const file = e.target.files?.[0];
    if (file) { onFile(file); e.target.value = ''; }
  }

  return (
    <div className={styles.zone} onClick={() => inputRef.current?.click()}>
      <input ref={inputRef} type="file" accept=".txt,.pdf,.md,.docx" style={{ display: 'none' }} onChange={handleChange} />
      <div className={styles.iconWrap}>
        <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      </div>
      <div className={styles.labels}>
        <span className={styles.primary}>Choose a Document</span>
        <span className={styles.secondary}>PDF · TXT · MD · DOCX</span>
      </div>
    </div>
  );
}
