import { useState, useCallback, useEffect } from "react";
import { getDocuments, deleteDocument } from "../services/api";

export function useDocuments() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoad, setInitialLoad] = useState(true);
  const [token, setToken] = useState(localStorage.getItem("token"));

  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === "token" || !localStorage.getItem("token")) {
        setDocs([]); // Clear docs when token changes
        setToken(localStorage.getItem("token"));
      }
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const list = await getDocuments();
      setDocs(Array.isArray(list) ? list : []);
    } catch (error) {
      console.error("Failed to fetch documents:", error);
      setDocs([]);
    } finally {
      setInitialLoad(false);
    }
  }, []);

  const remove = useCallback(async (filename) => {
    setLoading(true);
    try {
      const status = await deleteDocument(filename);
      setDocs((prev) => prev.filter((d) => d !== filename));
      return { ok: true, status };
    } catch (err) {
      return { ok: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  return { docs, refresh, remove, loading, initialLoad };
}
