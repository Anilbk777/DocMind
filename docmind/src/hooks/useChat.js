import { useState, useCallback, useRef } from 'react';
import { streamChat } from '../services/api';
import { stripSources, extractSources } from '../utils/helpers';

export function useChat() {
  const [messages,  setMessages]  = useState([
    { id: 'greeting', role: 'ai', body: "Hello! I'm **DocMind** — ask anything about your uploaded documents and I'll search them first, then stream a clear answer in real time.", sources: [], streaming: false },
  ]);
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef(null);

  const send = useCallback(async (query, provider) => {
    if (streaming) return;

    // Add user message
    const userId = `u-${Date.now()}`;
    setMessages(prev => [...prev, { id: userId, role: 'user', body: query }]);

    // Add empty AI placeholder
    const aiId = `ai-${Date.now()}`;
    setMessages(prev => [...prev, { id: aiId, role: 'ai', body: '', sources: [], streaming: true }]);
    setStreaming(true);

    let raw = '';
    try {
      for await (const chunk of streamChat(query, provider)) {
        raw += chunk;
        const bodyOnly = stripSources(raw);
        setMessages(prev =>
          prev.map(m => m.id === aiId ? { ...m, body: bodyOnly } : m)
        );
      }
    } catch (err) {
      raw = `[Stream Error]: ${err.message}`;
      setMessages(prev =>
        prev.map(m => m.id === aiId ? { ...m, body: raw } : m)
      );
    } finally {
      const { body, sources } = extractSources(raw);
      setMessages(prev =>
        prev.map(m => m.id === aiId ? { ...m, body, sources, streaming: false } : m)
      );
      setStreaming(false);
    }
  }, [streaming]);

  return { messages, send, streaming };
}
