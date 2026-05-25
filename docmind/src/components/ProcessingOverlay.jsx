import styles from './ProcessingOverlay.module.css';

export default function ProcessingOverlay({ visible, filename, status, isError }) {
  return (
    <div className={`${styles.overlay} ${visible ? styles.visible : ''}`}>
      <div className={styles.card}>
        <div className={styles.spinner} />
        <div className={styles.info}>
          <p className={styles.title}>Processing Document</p>
          <p className={styles.filename}>{filename}</p>
        </div>
        <p className={`${styles.status} ${isError ? styles.error : ''}`}>{status}</p>
      </div>
    </div>
  );
}
