import UploadZone from "./UploadZone";
import DocumentList from "./DocumentList";
import ProcessingPanel from "./ProcessingPanel";
import styles from "./LibraryView.module.css";

export default function LibraryView({ 
  docs, 
  onFiles, 
  onDelete, 
  processingJobs, 
  onClearJobs, 
  isUploading 
}) {
  return (
    <div className={styles.libraryContainer}>
      <div className={styles.libraryContent}>
        <header className={styles.header}>
          <h1 className={styles.title}>My Library</h1>
          <p className={styles.subtitle}>Manage your documents and knowledge base for Retrieval Augmented Generation.</p>
        </header>

        <div className={styles.grid}>
          <div className={styles.stackGroup}>
            <section className={styles.card}>
              <h2 className={styles.cardTitle}>
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Upload Documents
              </h2>
              <UploadZone onFiles={onFiles} isUploading={isUploading} />
              <div style={{ marginTop: '20px' }}>
                <ProcessingPanel
                  processingJobs={processingJobs}
                  onClear={onClearJobs}
                />
              </div>
            </section>

            <div className={styles.infoBox}>
              <h3 className={styles.infoTitle}>Knowledge Storage</h3>
              <p className={styles.infoText}>
                Files uploaded here are processed and stored in a vector database. 
                When you ask questions in the chat, DocMind will search these documents 
                to provide accurate, context-aware answers.
              </p>
            </div>
          </div>

          <section className={styles.card}>
            <div className={styles.fileListHeader}>
              <h2 className={styles.cardTitle} style={{ marginBottom: 0 }}>
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                Uploaded Files
              </h2>
              <span className={styles.fileCount}>{docs.length} Files</span>
            </div>
            
            <div className={styles.listScroll}>
              <DocumentList docs={docs} onDelete={onDelete} />
              {docs.length === 0 && (
                <div className={styles.emptyState}>
                  <p>No documents uploaded yet.</p>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
