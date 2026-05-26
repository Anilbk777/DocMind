
import UploadZone from './UploadZone';
import DocumentList from './DocumentList';
import styles from './Sidebar.module.css';

export default function Sidebar({ docs, onFile, onDelete, isOpen, onClose }) {
  return (
    <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.pulse} />
          <p className={styles.brand}>
            Doc<span>Mind</span>
          </p>
        </div>

        {/* Close button — only visible on mobile */}
        <button className={styles.closeBtn} onClick={onClose} aria-label="Close sidebar">
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div className={styles.body}>
        <div className={styles.section}>
          <p className={styles.sectionLabel}>Knowledge Base</p>
          <div className={styles.divider} />
          <p className={styles.sectionHint}>Upload study materials into your vector memory store.</p>
        </div>

        <UploadZone onFile={onFile} />
        <DocumentList docs={docs} onDelete={onDelete} />
      </div>

      <div className={styles.footer}>
        <p className={styles.tip}>
          <span>Tip:</span> Searches your files first, then falls back to general knowledge.
        </p>
      </div>
    </aside>
  );
}