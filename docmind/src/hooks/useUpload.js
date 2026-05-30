import { useState, useCallback, useRef } from 'react';
import { uploadDocuments, connectBatchWebSocket } from '../services/api';

/**
 * useUpload — manages multi-file upload with real-time WebSocket progress.
 *
 * Job lifecycle:  queued → processing → completed | failed
 *
 * @param {Function} onSuccess — called each time a job completes (e.g. to refresh document list)
 * @returns {{ processingJobs: Array, upload: Function, clearJobs: Function }}
 */
export function useUpload(onSuccess) {
  const [processingJobs, setProcessingJobs] = useState([]);
  const wsRef = useRef(null);

  const upload = useCallback(async (files) => {
    // 1. Build initial job list — all start as "queued"
    const initialJobs = files.map(file => ({
      job_id: null,
      filename: file.name,
      status: 'queued',
      chunks_created: null,
      error: null,
    }));

    setProcessingJobs(initialJobs);

    // 2. Upload all files in a single request
    let batch;
    try {
      batch = await uploadDocuments(files);
    } catch (err) {
      // Entire upload failed — mark all as failed
      setProcessingJobs(prev =>
        prev.map(job => ({
          ...job,
          status: 'failed',
          error: err.message || 'Upload failed',
        }))
      );
      return;
    }

    // 3. Map batch response to jobs — update to "processing" with job_ids
    const { batch_id, jobs: serverJobs } = batch;

    setProcessingJobs(prev =>
      prev.map((job, idx) => {
        const serverJob = serverJobs[idx];
        if (serverJob) {
          return {
            ...job,
            job_id: serverJob.job_id,
            status: 'processing',
          };
        }
        // File was discarded by backend (exceeded MAX_FILES_PER_BATCH)
        return {
          ...job,
          status: 'failed',
          error: 'Discarded — too many files in batch',
        };
      })
    );

    // 4. Connect WebSocket for real-time progress
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = connectBatchWebSocket(
      batch_id,
      // onMessage — fired once per finished job
      (data) => {
        const { job_id, status, chunks_created, error } = data;

        setProcessingJobs(prev =>
          prev.map(job => {
            if (job.job_id !== job_id) return job;
            return {
              ...job,
              status,
              chunks_created: chunks_created ?? null,
              error: error ?? null,
            };
          })
        );

        // Refresh document list when a job completes
        if (status === 'completed') {
          onSuccess?.();
        }
      },
      // onClose — WebSocket disconnected (all jobs done or error)
      () => {
        // Safety net: any job still "processing" → mark as failed
        setProcessingJobs(prev =>
          prev.map(job =>
            job.status === 'processing'
              ? { ...job, status: 'failed', error: 'Connection lost' }
              : job
          )
        );
        wsRef.current = null;
      }
    );

    wsRef.current = ws;
  }, [onSuccess]);

  // Allow the user to dismiss the processing panel after all jobs are terminal
  const clearJobs = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setProcessingJobs([]);
  }, []);

  return { processingJobs, upload, clearJobs };
}
