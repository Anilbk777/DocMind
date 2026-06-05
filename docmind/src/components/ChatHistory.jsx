import styles from "./ChatHistory.module.css";

export default function ChatHistory({ sessions, currentSessionId, onSessionClick, onNewChat, onDelete }) {
  return (
    <div className={styles.historyContainer}>
      <header className={styles.historyHeader}>
        <h3 className={styles.historyTitle}>History</h3>
        <button 
          onClick={onNewChat}
          className={styles.newChatBtn}
          title="New Chat"
        >
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </header>
      
      <div className={styles.sessionList + " custom-scrollbar"}>
        {sessions.length === 0 ? (
          <p className={styles.emptyState}>No history yet.</p>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => onSessionClick(session.id)}
              className={`${styles.sessionItem} ${currentSessionId === session.id ? styles.sessionItemActive : ""}`}
            >
              <svg 
                className={styles.sessionIcon} 
                width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <span className={styles.sessionTitle}>{session.title || "New Chat"}</span>
              
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(session.id);
                }}
                className={styles.deleteBtn}
                title="Delete Chat"
              >
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          ))
        )}
      </div>
      <div className={styles.divider}></div>
    </div>
  );
}
