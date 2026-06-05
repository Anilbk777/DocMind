const API_BASE = "http://127.0.0.1:8000/api/v1";
const WS_BASE = "ws://127.0.0.1:8000/api/v1";
/**
 * Upload multiple files in a single request.
 * Backend expects key "files" (plural) for list[UploadFile].
 * Returns: { batch_id, jobs: [{ job_id, filename }], accepted, discarded, ... }
 */
export async function register(name, email, password) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: name, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Registration failed (${res.status})`);
  }
  return await res.json();
}
export async function login(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `username=${email}&password=${password}`,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    console.log(err);
    throw new Error(err.detail || `Login failed (${res.status})`);
  }
  return await res.json();
}

export async function getMe() {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("No token found");
  }
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch user: ${res.status}`);
  }
  return await res.json();
}

export async function uploadDocuments(files) {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("No token found");
  }
  const fd = new FormData();
  files.forEach((file) => fd.append("files", file));
  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: fd,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }
  return await res.json();
}

/**
 * Open a WebSocket to track batch processing progress.
 *
 * Backend sends one JSON message per finished job:
 *   { job_id, filename, status: "completed"|"failed", chunks_created?, error? }
 * Server closes the connection after the last job finishes.
 *
 * @param {string}   batchId   - The batch_id from the upload response
 * @param {Function} onMessage - Called with parsed job status object
 * @param {Function} onClose   - Called when connection closes (all done or error)
 * @returns {{ close: Function }} - Call close() to disconnect early
 */
export function connectBatchWebSocket(batchId, onMessage, onClose) {
  const ws = new WebSocket(`${WS_BASE}/ws/batch/${batchId}`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (err) {
      console.error("[WS] Failed to parse message:", err);
    }
  };

  ws.onclose = () => {
    onClose?.();
  };

  ws.onerror = (err) => {
    console.error("[WS] WebSocket error:", err);
  };

  return {
    close: () => {
      if (
        ws.readyState === WebSocket.OPEN ||
        ws.readyState === WebSocket.CONNECTING
      ) {
        ws.close();
      }
    },
  };
}

export async function getDocuments() {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("No token found");
  }
  const res = await fetch(`${API_BASE}/documents`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error("Failed to fetch documents");
  const data = await res.json();
  // normalise: API may return string[] or object[]
  return (Array.isArray(data) ? data : []).map((d) =>
    typeof d === "string"
      ? d
      : (d.filename ?? d.file_name ?? d.name ?? String(d)),
  );
}

export async function deleteDocument(filename) {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("No token found");
  }
  const res = await fetch(
    `${API_BASE}/documents/${encodeURIComponent(filename)}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
  if (!res.ok && res.status !== 204) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Delete failed (${res.status})`);
  }
  return res.status;
}

export async function getChatSessions() {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No token found");
  const res = await fetch(`${API_BASE}/sessions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch chat sessions");
  return await res.json();
}

export async function getChatMessages(sessionId, limit = 10, offset = 0) {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No token found");
  const res = await fetch(
    `${API_BASE}/sessions/${sessionId}/messages?limit=${limit}&offset=${offset}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok) throw new Error("Failed to fetch messages");
  return await res.json();
}

export async function* streamChat(query, provider, sessionId = null) {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("No token found");
  }
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, provider, session_id: sessionId }),
  });
  if (!res.ok) throw new Error("Connection failed");

  // Capture the session ID from headers if provided by server
  const serverSessionId = res.headers.get("X-Chat-Session-ID");
  
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  
  // We yield the session ID first so the hook can capture it
  if (serverSessionId) {
    yield { type: "session_id", value: serverSessionId };
  }

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    yield { type: "chunk", value: decoder.decode(value, { stream: true }) };
  }
}
export async function deleteChatSession(sessionId) {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No token found");
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Delete failed (${res.status})`);
  }
  return res.status;
}
