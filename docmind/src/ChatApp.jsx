import { useEffect, useState, useCallback } from "react";
import { useNavigate, Routes, Route, Navigate } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import { getMe } from "./services/api";
import ChatView from "./components/ChatView";
import LibraryView from "./components/LibraryView";
import ConfirmationModal from "./components/ConfirmationModal";

import { useDocuments } from "./hooks/useDocuments";
import { useChat } from "./hooks/useChat";
import { useUpload } from "./hooks/useUpload";

import "./styles/globals.css";
import styles from "./ChatApp.module.css";

export default function ChatApp() {
  const { docs, refresh, remove } = useDocuments();
  const {
    messages,
    send,
    streaming,
    sessions,
    currentSessionId,
    loadHistory,
    startNewChat,
    deleteSession,
    hasMore,
    loadMore,
    loadingHistory
  } = useChat();
  const { processingJobs, upload, clearJobs, isUploading } = useUpload(refresh);
  const [user, setUser] = useState(null);

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const navigate = useNavigate();

  // Load documents and user when component mounts
  useEffect(() => {
    refresh();
    getMe().then(setUser).catch(console.error);
  }, [refresh]);

  const handleSessionSelect = useCallback((id) => {
    loadHistory(id);
    navigate("/app/chat");
    if (window.innerWidth < 768) setSidebarOpen(false);
  }, [loadHistory, navigate]);

  const handleNewChat = useCallback(() => {
    startNewChat();
    navigate("/app/chat");
    if (window.innerWidth < 768) setSidebarOpen(false);
  }, [startNewChat, navigate]);

  const handleDeleteRequest = useCallback((id) => {
    setSessionToDelete(id);
  }, []);

  const handleConfirmDelete = async () => {
    // Guard clause to prevent double execution if already processing
    if (!sessionToDelete || isDeleting) return;

    setIsDeleting(true);
    try {
      await deleteSession(sessionToDelete);
      setSessionToDelete(null); // Close modal on success
    } catch (error) {
      console.error("Failed to delete session:", error);
      // Keep modal open if you want them to be able to try again on error
    } finally {
      setIsDeleting(false); // Reset loading state
    }
  };

  const handleCancelDelete = () => {
    setSessionToDelete(null);
  };

  function handleLogout() {
    localStorage.removeItem("token");
    window.dispatchEvent(new Event("storage"));
    navigate("/login");
  }

  const handleBackdropClick = useCallback(() => setSidebarOpen(false), []);

  return (
    <div className={styles.appContainer}>
      {sidebarOpen && (
        <div className={styles.backdrop} onClick={handleBackdropClick} />
      )}

      <div className={styles.shell}>
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          onClose={() => setSidebarOpen(false)}
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSessionClick={handleSessionSelect}
          onNewChat={handleNewChat}
          onSessionDelete={handleDeleteRequest}
          user={user}
        />

        <div className={styles.chatCol}>
          <header className={styles.topbar}>
            <div className="flex items-center gap-3">
              <button
                className={styles.hamburger}
                onClick={() => setSidebarOpen(o => !o)}
                aria-label="toggle sidebar"
              >
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>

            <div className={styles.topbarTitleWrapper}>
              <span className={styles.topbarTitle}>
                {currentSessionId
                  ? sessions.find(s => s.id === currentSessionId)?.title || "Chat History"
                  : "New conversation"
                }
              </span>
            </div>

            <div className="flex items-center gap-3">
              <button onClick={handleLogout} className={styles.logoutBtnSmall} title="Logout">
                <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </header>

          <main className={styles.mainFrame}>
            <Routes>
              <Route path="chat" element={
                <ChatView
                  messages={messages}
                  send={send}
                  streaming={streaming}
                  loadMore={loadMore}
                  hasMore={hasMore}
                  loadingHistory={loadingHistory}
                />
              } />
              <Route path="library" element={
                <LibraryView
                  docs={docs}
                  onFiles={upload}
                  onDelete={remove}
                  processingJobs={processingJobs}
                  onClearJobs={clearJobs}
                  isUploading={isUploading}
                />
              } />
              <Route index element={<Navigate to="chat" replace />} />
            </Routes>
          </main>
        </div>
      </div>

      <ConfirmationModal
        isOpen={!!sessionToDelete}
        title="Delete Chat Session?"
        message="Are you sure you want to delete this conversation? This action cannot be undone."
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        confirmText={isDeleting ? "Deleting..." : "Delete Session"}
        isLoading={isDeleting}
      />
    </div>
  );
}
