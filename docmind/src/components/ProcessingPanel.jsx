import styles from './ProcessingPanel.module.css';

/**
 * ProcessingPanel — renders per-file processing status cards inside the sidebar.
 *
 * Each job: { job_id, filename, status, chunks_created, error }
 * Statuses: "queued" | "processing" | "completed" | "failed"
 */
export default function ProcessingPanel({ processingJobs = [], onClear }) {
  if (processingJobs.length === 0) return null;

  const doneCount = processingJobs.filter(
    j => j.status === 'completed' || j.status === 'failed'
  ).length;
  const totalCount = processingJobs.length;
  const allDone = doneCount === totalCount;

  return (
    <div className={styles.panel}>
      {/* Header */}
      <div className={styles.header}>
        <div className={`${styles.headerIcon} ${allDone ? styles.headerIconDone : ''}`}>
          {allDone ? (
            <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="#4caf50">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : (
            <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: 'var(--rose)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          )}
        </div>

        <span className={styles.headerTitle}>
          {allDone ? 'Processing Complete' : 'Processing'}
        </span>

        <span className={styles.headerCount}>
          {doneCount}/{totalCount}
        </span>

        <button
          className={styles.dismissBtn}
          onClick={onClear}
          disabled={!allDone}
          title={allDone ? 'Dismiss' : 'Waiting for all jobs to finish...'}
          aria-label="Dismiss processing panel"
        >
          <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
              d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Job list */}
      <div className={styles.jobList}>
        {processingJobs.map((job, idx) => (
          <JobRow key={job.job_id || `job-${idx}`} job={job} />
        ))}
      </div>
    </div>
  );
}

function JobRow({ job }) {
  const { filename, status, chunks_created, error } = job;
  const base = filename.replace(/\.[^.]+$/, '');
  const ext = filename.split('.').pop().toUpperCase();

  return (
    <div className={styles.jobRow}>
      {/* Status icon */}
      <div className={`${styles.jobIcon} ${getIconClass(status)}`}>
        {getIcon(status)}
      </div>

      {/* File info */}
      <div className={styles.jobInfo}>
        <span className={styles.jobFilename} title={filename}>
          {base}<span style={{ opacity: 0.4, fontSize: '9px', marginLeft: '3px' }}>.{ext}</span>
        </span>
        <span className={`${styles.jobStatus} ${status === 'failed' ? styles.jobStatusError : ''}`}>
          {getStatusText(status, error)}
        </span>
      </div>

      {/* Chunk badge (completed only) */}
      {status === 'completed' && chunks_created != null && (
        <span className={styles.chunkBadge}>
          {chunks_created} chunk{chunks_created !== 1 ? 's' : ''}
        </span>
      )}
    </div>
  );
}

function getIconClass(status) {
  switch (status) {
    case 'queued':     return styles.iconQueued;
    case 'processing': return styles.iconProcessing;
    case 'completed':  return styles.iconCompleted;
    case 'failed':     return styles.iconFailed;
    default:           return '';
  }
}

function getIcon(status) {
  switch (status) {
    case 'queued':
      return (
        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <circle cx="12" cy="12" r="10" strokeWidth="2" />
        </svg>
      );
    case 'processing':
      return (
        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      );
    case 'completed':
      return (
        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
            d="M5 13l4 4L19 7" />
        </svg>
      );
    case 'failed':
      return (
        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
            d="M6 18L18 6M6 6l12 12" />
        </svg>
      );
    default:
      return null;
  }
}

function getStatusText(status, error) {
  switch (status) {
    case 'queued':     return 'Waiting to upload...';
    case 'processing': return 'Ingesting into vector store...';
    case 'completed':  return 'Ready to chat';
    case 'failed':     return error || 'Processing failed';
    default:           return status;
  }
}
