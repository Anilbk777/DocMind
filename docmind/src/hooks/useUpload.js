import { useState, useCallback } from 'react';
import { uploadDocument } from '../services/api';

export function useUpload(onSuccess) {
  const [state, setState] = useState({ visible: false, filename: '', status: '', isError: false });

  const upload = useCallback(async (file) => {
    setState({ visible: true, filename: file.name, status: 'Chunking and embedding into vector store…', isError: false });
    try {
      await uploadDocument(file);
      setState(s => ({ ...s, status: 'Ingestion complete! Document is ready.' }));
      await delay(900);
      setState(s => ({ ...s, visible: false }));
      onSuccess?.();
    } catch (err) {
      setState(s => ({ ...s, status: `Error: ${err.message}`, isError: true }));
      await delay(2200);
      setState(s => ({ ...s, visible: false }));
    }
  }, [onSuccess]);

  return { overlayState: state, upload };
}

const delay = ms => new Promise(r => setTimeout(r, ms));
