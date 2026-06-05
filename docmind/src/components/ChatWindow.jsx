import { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import styles from './ChatWindow.module.css';

export default function ChatWindow({ messages, hasMore, onLoadMore, loadingMore }) {
  const bottomRef = useRef(null);
  const lastMessageCount = useRef(messages.length);

  useEffect(() => {
    // Only auto-scroll to bottom if the message count increased from the bottom (new messages)
    // not from the top (history loading)
    if (messages.length > lastMessageCount.current) {
      // Logic check: if history is loading, we don't automatically scroll to bottom
      // This is a naive check, better would be tracking if a new message was added to the end
      const lastMsgIsNew = messages[messages.length - 1]?.id !== lastMessageCount.current?.id;
      if (lastMsgIsNew && !loadingMore) {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
    }
    lastMessageCount.current = messages.length;
  }, [messages, loadingMore]);

  return (
    <div className={styles.window}>
      {hasMore && (
        <div className="flex justify-center py-4">
          <button 
            onClick={onLoadMore}
            disabled={loadingMore}
            className="text-xs text-rose-400 hover:text-rose-300 transition-colors bg-rose-500/10 px-3 py-1 rounded-full border border-rose-500/20 disabled:opacity-50"
          >
            {loadingMore ? "Loading history..." : "Load older messages"}
          </button>
        </div>
      )}
      
      {messages.map(msg => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
