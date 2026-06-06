import { useRef, useState } from 'react';
import styles from './UploadZone.module.css';

export default function UploadZone({ onFiles, isUploading }) {
  const inputRef = useRef(null);
  const [showLimit, setShowLimit] = useState(false);

  function handleChange(e) {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      let acceptedFiles = files;
      if (files.length > 5) {
        setShowLimit(true);
        acceptedFiles = files.slice(0, 5);
      }
      onFiles(acceptedFiles);
      e.target.value = "";
    }
  }

  return (
    <>
      {/* ── Limit Warning Modal ── */}
      {showLimit && (
        <div className={styles.overlay} onClick={() => setShowLimit(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalIcon}>
              <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                  d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
            </div>
            <h3 className={styles.modalTitle}>Upload limit reached</h3>
            <p className={styles.modalBody}>
              You can upload up to <strong>5 files</strong> at a time. Only the first 5 files have been queued for processing.
            </p>
            <button className={styles.modalBtn} onClick={() => setShowLimit(false)}>
              Got it
            </button>
          </div>
        </div>
      )}

      <div
        className={`${styles.zone} ${isUploading ? styles.disabled : ""}`}
        onClick={() => !isUploading && inputRef.current?.click()}
        style={{
          opacity: isUploading ? 0.5 : 1,
          pointerEvents: isUploading ? "none" : "auto",
        }}
        title={isUploading ? "Please wait for current uploads to complete" : ""}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.pdf,.md,.docx"
          multiple
          disabled={isUploading}
          style={{ display: "none" }}
          onChange={handleChange}
        />
        <div className={styles.iconWrap}>
          <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <div className={styles.labels}>
          <span className={styles.primary}>
            {isUploading ? "Processing..." : "Choose a Document"}
          </span>
          <span className={styles.secondary}>PDF · TXT · MD · DOCX</span>
        </div>
      </div>
    </>
  );
}
