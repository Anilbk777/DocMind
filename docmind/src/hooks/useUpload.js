
import { useState, useCallback, useRef } from "react";
import { uploadDocuments, connectBatchWebSocket } from "../services/api";

export function useUpload(onSuccess) {
  const [processingJobs, setProcessingJobs] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const wsRef = useRef(null);

  const upload = useCallback(
    async (files) => {
      if (isUploading || processingJobs.length > 0) {
        alert(
          "Please wait for current uploads to complete before uploading new documents.",
        );
        return;
      }

      setIsUploading(true);

      const initialJobs = files.map((file) => ({
        job_id: null,
        filename: file.name,
        status: "queued",
        chunks_created: null,
        error: null,
      }));

      setProcessingJobs(initialJobs);

      let batch;
      try {
        batch = await uploadDocuments(files);
      } catch (err) {
        setProcessingJobs((prev) =>
          prev.map((job) => ({
            ...job,
            status: "failed",
            error: err.message || "Upload failed",
          })),
        );
        setIsUploading(false);
        return;
      }

      const { batch_id, jobs: serverJobs } = batch;

      setProcessingJobs((prev) =>
        prev.map((job, idx) => {
          const serverJob = serverJobs[idx];
          if (serverJob) {
            return {
              ...job,
              job_id: serverJob.job_id,
              status: "processing",
            };
          }
          return {
            ...job,
            status: "failed",
            error: "Discarded — too many files in batch",
          };
        }),
      );

      if (wsRef.current) {
        wsRef.current.close();
      }

      const ws = connectBatchWebSocket(
        batch_id,
        (data) => {
          const { job_id, status, chunks_created, error } = data;

          setProcessingJobs((prev) => {
            const updated = prev.map((job) => {
              if (job.job_id !== job_id) return job;
              return {
                ...job,
                status,
                chunks_created: chunks_created ?? null,
                error: error ?? null,
              };
            });

            // Check if all jobs are terminal (completed or failed)
            const allDone = updated.every(
              (job) => job.status === "completed" || job.status === "failed",
            );

            if (allDone) {
              setIsUploading(false);
            }

            return updated;
          });

          if (status === "completed") {
            onSuccess?.();
          }
        },
        () => {
          setProcessingJobs((prev) =>
            prev.map((job) =>
              job.status === "processing"
                ? { ...job, status: "failed", error: "Connection lost" }
                : job,
            ),
          );
          wsRef.current = null;
          setIsUploading(false);
        },
      );

      wsRef.current = ws;
    },
    [isUploading, processingJobs.length, onSuccess],
  );

  const clearJobs = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setProcessingJobs([]);
    setIsUploading(false);
  }, []);

  return { processingJobs, upload, clearJobs, isUploading };
}
