import { useEffect } from 'react';
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

  // Load documents on mount
  useEffect(() => { refresh(); }, [refresh]);

  async function handleFile(file) {
    await upload(file);
  }

  async function handleDelete(filename) {
    const result = await remove(filename);
    if (!result.ok) {
      console.warn('Delete failed:', result.error);
    }
  }

  return (
    <>
      <ProcessingOverlay
        visible={overlayState.visible}
        filename={overlayState.filename}
        status={overlayState.status}
        isError={overlayState.isError}
      />

      <div className={styles.shell}>
        <Sidebar docs={docs} onFile={handleFile} onDelete={handleDelete} />

        <div className={styles.chatCol}>
          {/* Top bar */}
          <div className={styles.topbar}>
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
