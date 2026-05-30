const API_BASE = 'http://127.0.0.1:8000/api/v1';
const WS_BASE = 'ws://127.0.0.1:8000/api/v1';

/**
 * Upload multiple files in a single request.
 * Backend expects key "files" (plural) for list[UploadFile].
 * Returns: { batch_id, jobs: [{ job_id, filename }], accepted, discarded, ... }
 */
export async function uploadDocuments(files) {
  const fd = new FormData();
  files.forEach(file => fd.append('files', file));
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: fd });
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
      console.error('[WS] Failed to parse message:', err);
    }
  };

  ws.onclose = () => {
    onClose?.();
  };

  ws.onerror = (err) => {
    console.error('[WS] WebSocket error:', err);
  };

  return {
    close: () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    },
  };
}

export async function getDocuments() {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  const data = await res.json();
  // normalise: API may return string[] or object[]
  return (Array.isArray(data) ? data : []).map(d =>
    typeof d === 'string' ? d : (d.filename ?? d.file_name ?? d.name ?? String(d))
  );
}

export async function deleteDocument(filename) {
  const res = await fetch(`${API_BASE}/documents/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
  if (!res.ok && res.status !== 204) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Delete failed (${res.status})`);
  }
  return res.status;
}

export async function* streamChat(query, provider) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, provider }),
  });
  if (!res.ok) throw new Error('Connection failed');
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    yield decoder.decode(value, { stream: true });
  }
}
