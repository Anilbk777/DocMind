import { useState, useCallback, useRef, useEffect } from "react";
import { streamChat } from "../services/api";
import { stripSources, extractSources } from "../utils/helpers";

export function useChat() {
  const [messages, setMessages] = useState([
    {
      id: "greeting",
      role: "ai",
      body: "Hello! I'm **DocMind** — ask anything about your uploaded documents and I'll search them first, then stream a clear answer in real time.",
      sources: [],
      streaming: false,
    },
  ]);
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef(null);

  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === "token" || !localStorage.getItem("token")) {
        setMessages([]); // Clear messages on logout/token change
      }
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const send = useCallback(
    async (query, provider) => {
      if (streaming) return;

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
        for await (const chunk of streamChat(query, provider)) {
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
    [streaming],
  );

  return { messages, send, streaming };
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
