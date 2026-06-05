import { useState } from 'react';
import { extColor } from '../utils/helpers';
import styles from './DocumentList.module.css';

function DocItem({ filename, onDelete }) {
  const [deleting, setDeleting] = useState(false);
  const ext  = filename.split('.').pop().toUpperCase();
  const base = filename.replace(/\.[^.]+$/, '');
  const color = extColor(filename);

  async function handleDelete() {
    setDeleting(true);
    await onDelete(filename);
  }

  return (
    <div className={`${styles.item} ${deleting ? styles.deleting : ''} fadein`}>
      <div className={styles.icon}>
        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color }}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
      </div>
      <span className={styles.name} title={filename}>{base}</span>
      <span className={styles.ext}>{ext}</span>
      <button className={styles.deleteBtn} title={`Delete ${filename}`} onClick={handleDelete} disabled={deleting}>
        <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
        </svg>
      </button>
    </div>
  );
}

export default function DocumentList({ docs, onDelete }) {
  return (
    <div className={styles.list}>
      {docs.length === 0
        ? <p className={styles.empty}>No documents yet</p>
        : docs.map(f => <DocItem key={f} filename={f} onDelete={onDelete} />)
      }
    </div>
  );
}
