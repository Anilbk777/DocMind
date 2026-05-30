import { useState, useCallback } from 'react';
import { getDocuments, deleteDocument } from '../services/api';

export function useDocuments() {
  const [docs,        setDocs]        = useState([]);
  const [loading,     setLoading]     = useState(false);
  const [initialLoad, setInitialLoad] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const list = await getDocuments();
      setDocs(list);
    } catch {
      // silently ignore if endpoint isn't ready yet
    } finally {
      setInitialLoad(false);
    }
  }, []);

  const remove = useCallback(async (filename) => {
    setLoading(true);
    try {
      const status = await deleteDocument(filename);
      // 200, 204, 404 all mean "gone"
      setDocs(prev => prev.filter(d => d !== filename));
      return { ok: true, status };
    } catch (err) {
      return { ok: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  return { docs, refresh, remove, loading, initialLoad };
}
