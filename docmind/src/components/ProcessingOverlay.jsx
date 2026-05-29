import styles from './ProcessingOverlay.module.css';

export default function ProcessingOverlay({ visible, jobs = [] }) {
  return (
    <div className={`${styles.overlay} ${visible ? styles.visible : ''}`}>
      <div className={styles.card}>
        <div className={styles.spinner} />
        <div className={styles.info}>
          <p className={styles.title}>Processing Documents</p>
          <ul style={{ listStyle: 'none', padding: 0, margin: '10px 0' }}>
            {jobs.map((job, idx) => (
              <li key={idx} style={{ marginBottom: '8px' }}>
                <p className={styles.filename}>{job.filename}</p>
                <p className={`${styles.status} ${job.isError ? styles.error : ''}`} style={{ fontSize: '0.85rem' }}>
                  {job.status}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
