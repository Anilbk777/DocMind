// import { useEffect } from 'react';
// import Sidebar from './components/Sidebar';
// import ChatWindow from './components/ChatWindow';
// import ChatInput from './components/ChatInput';
// import ProcessingOverlay from './components/ProcessingOverlay';
// import { useDocuments } from './hooks/useDocuments';
// import { useChat } from './hooks/useChat';
// import { useUpload } from './hooks/useUpload';
// import './styles/globals.css';
// import styles from './App.module.css';

// export default function App() {
//   const { docs, refresh, remove } = useDocuments();
//   const { messages, send, streaming } = useChat();
//   const { overlayState, upload } = useUpload(refresh);

//   // Load documents on mount
//   useEffect(() => { refresh(); }, [refresh]);

//   async function handleFile(file) {
//     await upload(file);
//   }

//   async function handleDelete(filename) {
//     const result = await remove(filename);
//     if (!result.ok) {
//       console.warn('Delete failed:', result.error);
//     }
//   }

//   return (
//     <>
//       <ProcessingOverlay
//         visible={overlayState.visible}
//         filename={overlayState.filename}
//         status={overlayState.status}
//         isError={overlayState.isError}
//       />

//       <div className={styles.shell}>
//         <Sidebar docs={docs} onFile={handleFile} onDelete={handleDelete} />

//         <div className={styles.chatCol}>
//           {/* Top bar */}
//           <div className={styles.topbar}>
//             <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: 'var(--rose)', flexShrink: 0 }}>
//               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
//                 d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
//             </svg>
//             <span className={styles.topbarTitle}>New conversation</span>
//           </div>

//           <ChatWindow messages={messages} />
//           <ChatInput onSend={send} disabled={streaming} />
//         </div>
//       </div>
//     </>
//   );
// }


// ====================================================================================================

import { useEffect, useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import ProcessingOverlay from './components/ProcessingOverlay';
import { useDocuments } from './hooks/useDocuments';
import { useChat } from './hooks/useChat';
import { useUpload } from './hooks/useUpload';
import './styles/globals.css';
import styles from './App.module.css';

export default function App() {
  const { docs, refresh, remove } = useDocuments();
  const { messages, send, streaming } = useChat();
  const { overlayState, upload } = useUpload(refresh);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => { refresh(); }, [refresh]);

  // Close sidebar when clicking backdrop
  const handleBackdropClick = useCallback(() => setSidebarOpen(false), []);

  // Close sidebar on route/resize back to desktop
  useEffect(() => {
    function onResize() {
      if (window.innerWidth > 768) setSidebarOpen(false);
    }
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  async function handleFile(file) {
    await upload(file);
    setSidebarOpen(false);
  }

  async function handleDelete(filename) {
    const result = await remove(filename);
    if (!result.ok) console.warn('Delete failed:', result.error);
  }

  return (
    <>
      <ProcessingOverlay
        visible={overlayState.visible}
        filename={overlayState.filename}
        status={overlayState.status}
        isError={overlayState.isError}
      />

      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div className={styles.backdrop} onClick={handleBackdropClick} />
      )}

      <div className={styles.shell}>
        <Sidebar
          docs={docs}
          onFile={handleFile}
          onDelete={handleDelete}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        <div className={styles.chatCol}>
          {/* Top bar */}
          <div className={styles.topbar}>
            {/* Hamburger — mobile only */}
            <button
              className={styles.hamburger}
              onClick={() => setSidebarOpen(o => !o)}
              aria-label="Toggle sidebar"
            >
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"/>
              </svg>
            </button>

            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: 'var(--rose)', flexShrink: 0 }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
            </svg>
            <span className={styles.topbarTitle}>New conversation</span>
          </div>

          <ChatWindow messages={messages} />
          <ChatInput onSend={send} disabled={streaming} />
        </div>
      </div>
    </>
  );
}