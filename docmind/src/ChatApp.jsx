// import { useEffect, useState, useCallback } from "react";
// import { useNavigate } from "react-router-dom";
// import Sidebar from "./components/Sidebar";
// import ChatWindow from "./components/ChatWindow";
// import ChatInput from "./components/ChatInput";
// import { useDocuments } from "./hooks/useDocuments";
// import { useChat } from "./hooks/useChat";
// import { useUpload } from "./hooks/useUpload";
// import "./styles/globals.css";
// import styles from "./ChatApp.module.css";

// export default function App() {
//   const { docs, refresh, remove } = useDocuments();
//   const { messages, send, streaming } = useChat();
//   const { processingJobs, upload, clearJobs, isUploading } = useUpload(refresh);
//   const [sidebarOpen, setSidebarOpen] = useState(false);
//   const navigate = useNavigate();
//   function handleLogout() {
//     localStorage.removeItem("token");

//     // Trigger storage event in all tabs
//     window.dispatchEvent(
//       new StorageEvent("storage", {
//         key: "token",
//         newValue: null,
//         oldValue: localStorage.getItem("token"),
//         storageArea: localStorage,
//       }),
//     );

//     navigate("/login");
//   }

//   useEffect(() => {
//     refresh();
//   }, [refresh]);

//   useEffect(() => {
//     const handleStorageChange = (e) => {
//       if (e.key === "token") {
//         if (localStorage.getItem("token")) {
//           // New token set, refresh documents for new user
//           refresh();
//         }
//       }
//     };
//     window.addEventListener("storage", handleStorageChange);
//     return () => window.removeEventListener("storage", handleStorageChange);
//   }, [refresh]);

//   // Close sidebar when clicking backdrop
//   const handleBackdropClick = useCallback(() => setSidebarOpen(false), []);

//   // Close sidebar on route/resize back to desktop
//   useEffect(() => {
//     function onResize() {
//       if (window.innerWidth > 768) setSidebarOpen(false);
//     }
//     window.addEventListener("resize", onResize);
//     return () => window.removeEventListener("resize", onResize);
//   }, []);

//   async function handleFiles(files) {
//     await upload(files);
//     setSidebarOpen(false);
//   }

//   async function handleDelete(filename) {
//     const result = await remove(filename);
//     if (!result.ok) console.warn("Delete failed:", result.error);
//   }

//   return (
//     <>
//       {/* Mobile backdrop */}
//       {sidebarOpen && (
//         <div className={styles.backdrop} onClick={handleBackdropClick} />
//       )}

//       <div className={styles.shell}>
//         <Sidebar
//           docs={docs}
//           onFiles={handleFiles}
//           onDelete={handleDelete}
//           isOpen={sidebarOpen}
//           onClose={() => setSidebarOpen(false)}
//           processingJobs={processingJobs}
//           onClearJobs={clearJobs}
//           isUploading={isUploading}
//         />

//         <div className={styles.chatCol}>
//           {/* Top bar */}
//           <div className={styles.topbar}>
//             {/* Hamburger — mobile only */}
//             <button
//               className={styles.hamburger}
//               onClick={() => setSidebarOpen((o) => !o)}
//               aria-label="Toggle sidebar"
//             >
//               <svg
//                 width="18"
//                 height="18"
//                 fill="none"
//                 viewBox="0 0 24 24"
//                 stroke="currentColor"
//               >
//                 <path
//                   strokeLinecap="round"
//                   strokeLinejoin="round"
//                   strokeWidth="2"
//                   d="M4 6h16M4 12h16M4 18h16"
//                 />
//               </svg>
//             </button>

//             <svg
//               width="16"
//               height="16"
//               fill="none"
//               viewBox="0 0 24 24"
//               stroke="currentColor"
//               style={{ color: "var(--rose)", flexShrink: 0 }}
//             >
//               <path
//                 strokeLinecap="round"
//                 strokeLinejoin="round"
//                 strokeWidth="2"
//                 d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
//               />
//             </svg>
//             <div
//               style={{
//                 display: "flex",
//                 justifyContent: "space-between",
//                 alignItems: "center",
//                 width: "100%",
//                 marginLeft: "16px",
//                 marginRight: "16px",
//               }}
//             >
//               <span className={styles.topbarTitle}>New conversation</span>
//               <button
//                 onClick={handleLogout}
//                 aria-label="logout"
//                 style={{
//                   backgroundColor: "var(--rose)",
//                   color: "white",
//                   border: "none",
//                   padding: "8px 16px",
//                   borderRadius: "8px",
//                   cursor: "pointer",
//                   display: "flex",
//                   alignItems: "center",
//                   gap: "8px",
//                   transition: "all 0.2s ease",
//                 }}
//                 onMouseEnter={(e) => {
//                   e.currentTarget.style.transform = "scale(1.05)";
//                   e.currentTarget.style.backgroundColor = "var(-dark)";
//                 }}
//                 onMouseLeave={(e) => {
//                   e.currentTarget.style.transform = "scale(1)";
//                   e.currentTarget.style.backgroundColor = "var(--rose)";
//                 }}
//               >
//                 <svg
//                   width="18"
//                   height="18"
//                   fill="none"
//                   viewBox="0 0 24 24"
//                   stroke="currentColor"
//                 >
//                   <path
//                     strokeLinecap="round"
//                     strokeLinejoin="round"
//                     strokeWidth="2"
//                     d="M17 16l4-4m0 0l-4-4m4 4H7"
//                   />
//                 </svg>
//                 Logout
//               </button>
//             </div>
//           </div>

//           <ChatWindow messages={messages} />
//           <ChatInput onSend={send} disabled={streaming} />
//         </div>
//       </div>
//     </>
//   );
// }

import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
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
    hasMore,
    loadMore,
    loadingHistory,
    deleteSession
  } = useChat();
  const { processingJobs, upload, clearJobs, isUploading } = useUpload(refresh);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const navigate = useNavigate();

  // Load documents when component mounts
  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSessionSelect = useCallback((id) => {
    loadHistory(id);
    setSidebarOpen(false);
  }, [loadHistory]);

  const handleNewChat = useCallback(() => {
    startNewChat();
    setSidebarOpen(false);
  }, [startNewChat]);

  const handleDeleteRequest = useCallback((id) => {
    setSessionToDelete(id);
  }, []);

  const handleConfirmDelete = async () => {
    if (sessionToDelete) {
      await deleteSession(sessionToDelete);
      setSessionToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setSessionToDelete(null);
  };

  function handleLogout() {
    localStorage.removeItem("token");

    // Navigate away immediately
    navigate("/login", { replace: true });
  }

  const handleBackdropClick = useCallback(() => {
    setSidebarOpen(false);
  }, []);

  useEffect(() => {
    function onResize() {
      if (window.innerWidth > 768) {
        setSidebarOpen(false);
      }
    }

    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
    };
  }, []);

  async function handleFiles(files) {
    await upload(files);
    setSidebarOpen(false);
  }

  async function handleDelete(filename) {
    const result = await remove(filename);

    if (!result.ok) {
      console.warn("Delete failed:", result.error);
    }
  }

  return (
    <>
      {sidebarOpen && (
        <div className={styles.backdrop} onClick={handleBackdropClick} />
      )}

      <div className={styles.shell}>
        <Sidebar
          docs={docs}
          onFiles={handleFiles}
          onDelete={handleDelete}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          processingJobs={processingJobs}
          onClearJobs={clearJobs}
          isUploading={isUploading}
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSessionClick={handleSessionSelect}
          onNewChat={handleNewChat}
          onSessionDelete={handleDeleteRequest}
        />

        <div className={styles.chatCol}>
          <div className={styles.topbar}>
            <button
              className={styles.hamburger}
              onClick={() => setSidebarOpen((prev) => !prev)}
              aria-label="Toggle sidebar"
            >
              <svg
                width="18"
                height="18"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>

            <svg
              width="16"
              height="16"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              style={{
                color: "var(--rose)",
                flexShrink: 0,
              }}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                width: "100%",
                marginLeft: "16px",
                marginRight: "16px",
              }}
            >
              <span className={styles.topbarTitle}>
                {currentSessionId 
                  ? sessions.find(s => s.id === currentSessionId)?.title || "Chat History"
                  : "New conversation"
                }
              </span>

              <button
                onClick={handleLogout}
                aria-label="logout"
                style={{
                  backgroundColor: "var(--rose)",
                  color: "white",
                  border: "none",
                  padding: "8px 16px",
                  borderRadius: "8px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  transition: "all 0.2s ease",
                }}
              >
                <svg
                  width="18"
                  height="18"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M17 16l4-4m0 0l-4-4m4 4H7"
                  />
                </svg>
                Logout
              </button>
            </div>
          </div>
          <ChatWindow 
            messages={messages} 
            hasMore={hasMore}
            onLoadMore={loadMore}
            loadingMore={loadingHistory}
          />

          <ChatInput onSend={send} disabled={streaming} />
        </div>
      </div>

      <ConfirmationModal 
        isOpen={!!sessionToDelete}
        title="Delete Chat Session?"
        message="Are you sure you want to delete this conversation? This action cannot be undone."
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        confirmText="Delete Session"
      />
    </>
  );
}
