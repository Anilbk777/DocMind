import { useEffect, useState } from "react";
import UploadZone from "./UploadZone";
import DocumentList from "./DocumentList";
import ProcessingPanel from "./ProcessingPanel";
import ChatHistory from "./ChatHistory";
import styles from "./Sidebar.module.css";
import { getMe } from "../services/api";

export default function Sidebar({
  docs,
  onFiles,
  onDelete,
  isOpen,
  onClose,
  processingJobs,
  onClearJobs,
  isUploading,
  // New props for chat history
  sessions = [],
  currentSessionId = null,
  onSessionClick,
  onNewChat,
  onSessionDelete,
}) {
  const [user, setUser] = useState(null);
  const [userLoading, setUserLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then((data) => {
        setUser(data);
        setUserLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch user:", err);
        setUser(null);
        setUserLoading(false);
      });
  }, []);

  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === "token" || !localStorage.getItem("token")) {
        setUser(null);
      }
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  return (
    <aside className={`${styles.sidebar} ${isOpen ? styles.open : ""}`}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.pulse} />
          <p className={styles.brand}>
            Doc<span>Mind</span>
          </p>
        </div>

        {/* Close button — only visible on mobile */}
        <button
          className={styles.closeBtn}
          onClick={onClose}
          aria-label="Close sidebar"
        >
          <svg
            width="14"
            height="14"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
      {!userLoading && user && (
        <div
          style={{ padding: "0.5rem 1rem", textDecoration: "underline" }}
          className="flex justify-between items-center"
        >
          <p className="text-white text-lg font-bold">{user.username}</p>
        </div>
      )}
      <div className={styles.body}>
        <div className={styles.section}>
          <p className={styles.sectionLabel}>Knowledge Base</p>
          <div className={styles.divider} />
          <p className={styles.sectionHint}>
            Upload study materials into your vector memory store.
          </p>
        </div>

        <ChatHistory 
          sessions={sessions} 
          currentSessionId={currentSessionId}
          onSessionClick={onSessionClick}
          onNewChat={onNewChat}
          onDelete={onSessionDelete}
        />

        <UploadZone onFiles={onFiles} isUploading={isUploading} />

        {/* Processing panel — sticky so it stays visible during scrolling */}
        <div className={styles.processingPanelContainer}>
          <ProcessingPanel
            processingJobs={processingJobs}
            onClear={onClearJobs}
          />
        </div>

        <DocumentList docs={docs} onDelete={onDelete} />
      </div>

      <div className={styles.footer}>
        <p className={styles.tip}>
          <span>Tip:</span> Searches your files first, then falls back to
          general knowledge.
        </p>
      </div>
    </aside>
  );
}
