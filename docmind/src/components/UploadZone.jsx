import { useRef } from 'react';
import styles from './UploadZone.module.css';

export default function UploadZone({ onFiles }) {
  const inputRef = useRef(null);

  function handleChange(e) {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      let acceptedFiles = files;
      if (files.length > 5) {
        alert(`You can only upload up to 5 files at a time. Only the first 5 files will be processed.`);
        acceptedFiles = files.slice(0, 5);
      }
      onFiles(acceptedFiles);
      e.target.value = '';
    }
  }

  return (
    <div className={styles.zone} onClick={() => inputRef.current?.click()}>
      <input ref={inputRef} type="file" accept=".txt,.pdf,.md,.docx" multiple style={{ display: 'none' }} onChange={handleChange} />
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
