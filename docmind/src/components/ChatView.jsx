import ChatWindow from "./ChatWindow";
import ChatInput from "./ChatInput";
import styles from "../ChatApp.module.css";

export default function ChatView({ 
  messages, 
  send, 
  streaming, 
  loadMore, 
  hasMore, 
  loadingHistory 
}) {
  return (
    <div className={styles.chatViewWrapper}>
      <ChatWindow 
        messages={messages} 
        onLoadMore={loadMore} 
        hasMore={hasMore} 
        isLoadingMore={loadingHistory}
      />
      <div className={styles.inputWrapper}>
        <ChatInput onSend={send} disabled={streaming} />
      </div>
    </div>
  );
}
