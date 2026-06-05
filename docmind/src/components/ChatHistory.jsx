import styles from "./Sidebar.module.css";

export default function ChatHistory({ sessions, currentSessionId, onSessionClick, onNewChat, onDelete }) {
  return (
    <div className="mt-4">
      <div className="flex items-center justify-between px-1 mb-2">
        <h3 className="text-[10px] uppercase tracking-wider font-bold text-rose-500">History</h3>
        <button 
          onClick={onNewChat}
          className="p-1 hover:bg-gray-100 rounded-md text-gray-500 transition-colors"
          title="New Chat"
        >
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>
      
      <div className="flex flex-col gap-1 max-h-[300px] overflow-y-auto custom-scrollbar">
        {sessions.length === 0 ? (
          <p className="text-[11px] text-gray-400 px-1 italic">No history yet.</p>
        ) : (
          sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => onSessionClick(session.id)}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] transition-all border w-full relative ${
                currentSessionId === session.id 
                  ? "bg-rose-50 border-rose-100 text-rose-600 font-medium" 
                  : "bg-white border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-200"
              }`}
            >
              <svg 
                className={`flex-shrink-0 ${currentSessionId === session.id ? 'text-rose-400' : 'text-gray-300 group-hover:text-gray-400'}`} 
                width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <span className="truncate flex-1 pr-4">{session.title || "New Chat"}</span>
              
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(session.id);
                }}
                className="absolute right-2 opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-rose-600 transition-all"
                title="Delete Chat"
              >
                <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </button>
          ))
        )}
      </div>
      <div className="border-b border-gray-100 mt-4 mx-1"></div>
    </div>
  );
}
