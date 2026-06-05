import NavMenu from "./NavMenu";
import ChatHistory from "./ChatHistory";
import styles from "./Sidebar.module.css";

export default function Sidebar({
  isOpen,
  onClose,
  sessions = [],
  currentSessionId = null,
  onSessionClick,
  onNewChat,
  onSessionDelete,
  user
}) {
  return (
    <aside className={`${styles.sidebar} ${isOpen ? styles.open : ""}`}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.brandIcon}>
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
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
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div className={styles.body}>
        <NavMenu />

        <ChatHistory 
          sessions={sessions} 
          currentSessionId={currentSessionId}
          onSessionClick={onSessionClick}
          onNewChat={onNewChat}
          onDelete={onSessionDelete}
        />
      </div>

      <div className={styles.userSection}>
        {user && (
          <div className={styles.userCard}>
            <div className={styles.avatar}>
              {user.username?.charAt(0).toUpperCase() || "U"}
            </div>
            <div className={styles.userInfo}>
              <p className={styles.userName}>{user.username || "User"}</p>
              <p className={styles.userEmail}>{user.email || "guest@docmind"}</p>
            </div>
          </div>
        )}
        <div style={{ marginTop: '12px' }}>
         
        </div>
      </div>
    </aside>
  );
}
