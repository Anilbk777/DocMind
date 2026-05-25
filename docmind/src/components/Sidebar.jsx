import UploadZone from './UploadZone';
import DocumentList from './DocumentList';
import styles from './Sidebar.module.css';

export default function Sidebar({ docs, onFile, onDelete }) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <span className={styles.pulse} />
        <p className={styles.brand}>
          Doc<span>Mind</span>
        </p>
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
