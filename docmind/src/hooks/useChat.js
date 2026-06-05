import { useState, useCallback, useRef, useEffect } from "react";
import { streamChat, getChatSessions, getChatMessages } from "../services/api";
import { stripSources, extractSources } from "../utils/helpers";

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [streaming, setStreaming] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const offsetRef = useRef(0);

  const initialGreeting = {
    id: "greeting",
    role: "ai",
    body: "Hello! I'm **DocMind** — ask anything about your uploaded documents and I'll search them first, then stream a clear answer in real time.",
    sources: [],
    streaming: false,
  };

  const refreshSessions = useCallback(async () => {
    try {
      const data = await getChatSessions();
      setSessions(data);
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  }, []);

  const loadHistory = useCallback(async (sessionId) => {
    setLoadingHistory(true);
    try {
      const data = await getChatMessages(sessionId, 10, 0);
      const formatted = data.map(msg => {
        if (msg.role === "user") return { id: msg.id, role: "user", body: msg.content, sources: [], streaming: false };
        const { body, sources } = extractSources(msg.content);
        return {
          id: msg.id,
          role: msg.role,
          body,
          sources,
          streaming: false
        };
      });
      setMessages(formatted);
      setCurrentSessionId(sessionId);
      offsetRef.current = data.length;
      setHasMore(data.length === 10);
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  const loadMore = useCallback(async () => {
    if (!currentSessionId || !hasMore || loadingHistory) return;
    setLoadingHistory(true);
    try {
      const data = await getChatMessages(currentSessionId, 10, offsetRef.current);
      const formatted = data.map(msg => {
        if (msg.role === "user") return { id: msg.id, role: "user", body: msg.content, sources: [], streaming: false };
        const { body, sources } = extractSources(msg.content);
        return {
          id: msg.id,
          role: msg.role,
          body,
          sources,
          streaming: false
        };
      });
      setMessages(prev => [...formatted, ...prev]);
      offsetRef.current += data.length;
      setHasMore(data.length === 10);
    } catch (err) {
      console.error("Failed to load more:", err);
    } finally {
      setLoadingHistory(false);
    }
  }, [currentSessionId, hasMore, loadingHistory]);

  const startNewChat = useCallback(() => {
    setCurrentSessionId(null);
    setMessages([initialGreeting]);
    offsetRef.current = 0;
    setHasMore(false);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      refreshSessions();
      setMessages([initialGreeting]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  const send = useCallback(
    async (query, provider) => {
      if (streaming) return;
      console.log("[Chat] Sending message. Current Session ID:", currentSessionId);

      // Add user message
      const userId = `u-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: userId, role: "user", body: query },
      ]);

      // Add empty AI placeholder
      const aiId = `ai-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: aiId, role: "ai", body: "", sources: [], streaming: true },
      ]);
      setStreaming(true);

      let raw = "";
      try {
        for await (const res of streamChat(query, provider, currentSessionId)) {
          if (res.type === "session_id") {
            console.log("[Chat] Received Session ID from server:", res.value);
            setCurrentSessionId(res.value);
            refreshSessions(); // Refresh list if a new session was created
            continue;
          }
          
          const chunk = res.value;
          raw += chunk;
          const bodyOnly = stripSources(raw);
          setMessages((prev) =>
            prev.map((m) => (m.id === aiId ? { ...m, body: bodyOnly } : m)),
          );
        }
      } catch (err) {
        raw = `[Stream Error]: ${err.message}`;
        setMessages((prev) =>
          prev.map((m) => (m.id === aiId ? { ...m, body: raw } : m)),
        );
      } finally {
        const { body, sources } = extractSources(raw);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiId ? { ...m, body, sources, streaming: false } : m,
          ),
        );
        setStreaming(false);
      }
    },
    [streaming, currentSessionId, refreshSessions],
  );

  const deleteSession = useCallback(async (sessionId) => {
    try {
      const { deleteChatSession } = await import("../services/api");
      await deleteChatSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        startNewChat();
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  }, [currentSessionId, startNewChat]);

  return {
    messages,
    send,
    streaming,
    sessions,
    currentSessionId,
    loadHistory,
    loadMore,
    hasMore,
    loadingHistory,
    startNewChat,
    deleteSession
  };
}

// import { useState, useEffect, useCallback } from "react";
// import { streamChat } from "../services/api";

// export function useChat() {
//   const [messages, setMessages] = useState([]);
//   const [streaming, setStreaming] = useState(false);

//   // Clear messages when token changes
//   useEffect(() => {
//     const handleStorageChange = (e) => {
//       if (e.key === "token" || !localStorage.getItem("token")) {
//         setMessages([]); // Clear messages on logout/token change
//       }
//     };
//     window.addEventListener("storage", handleStorageChange);
//     return () => window.removeEventListener("storage", handleStorageChange);
//   }, []);

//   const send = useCallback(async (query, provider) => {
//     setMessages((prev) => [...prev, { role: "user", content: query }]);
//     setStreaming(true);

//     try {
//       let fullResponse = "";
//       for await (const chunk of streamChat(query, provider)) {
//         fullResponse += chunk;
//         setMessages((prev) => {
//           const updated = [...prev];
//           updated[updated.length - 1] = {
//             role: "assistant",
//             content: fullResponse,
//           };
//           return updated;
//         });
//       }
//     } catch (error) {
//       console.error("Chat error:", error);
//       setMessages((prev) => [
//         ...prev,
//         { role: "assistant", content: "Error: " + error.message },
//       ]);
//     } finally {
//       setStreaming(false);
//     }
//   }, []);

//   return { messages, send, streaming };
// }
