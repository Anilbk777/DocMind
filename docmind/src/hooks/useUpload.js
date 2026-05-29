import { useState, useCallback } from 'react';
import { uploadDocument, getJobStatus } from '../services/api';

export function useUpload(onSuccess) {
  const [state, setState] = useState({ visible: false, jobs: [] });

  const upload = useCallback(async (files) => {
    // Initialize state with all files
    const initialJobs = files.map(file => ({
      filename: file.name,
      status: 'Uploading...',
      isError: false,
      jobId: null,
      completed: false
    }));
    
    setState({ visible: true, jobs: initialJobs });

    // Step 1: Upload all files concurrently to get job IDs
    const uploadPromises = files.map(async (file, index) => {
      try {
        const uploadRes = await uploadDocument(file);
        return { index, jobId: uploadRes.job_id, status: 'Processing in background...', isError: false };
      } catch (err) {
        return { index, jobId: null, status: `Error: ${err.message}`, isError: true, completed: true };
      }
    });

    const uploadResults = await Promise.all(uploadPromises);

    // Update state with job IDs
    setState(s => {
      const newJobs = [...s.jobs];
      uploadResults.forEach(res => {
        newJobs[res.index] = { ...newJobs[res.index], ...res };
      });
      return { ...s, jobs: newJobs };
    });

    // Close the modal shortly after uploads are queued, if we want them to go to background
    await delay(1500);
    setState(s => ({ ...s, visible: false }));

    // Step 2: Polling loop
    let activeJobIds = uploadResults.filter(r => r.jobId && !r.isError).map(r => r.jobId);
    
    if (activeJobIds.length === 0) return; // All failed during upload

    const poll = async () => {
      try {
        const statuses = await Promise.all(activeJobIds.map(getJobStatus));
        let anyChanges = false;
        let allDone = true;

        const statusMap = {};
        statuses.forEach(j => { statusMap[j.job_id] = j; });

        setState(s => {
          const newJobs = s.jobs.map(job => {
            if (!job.jobId || job.completed) return job;
            const updated = statusMap[job.jobId];
            if (!updated) return job; // Should not happen

            if (updated.status === 'completed') {
              anyChanges = true;
              return { ...job, status: 'Ingestion complete!', completed: true };
            } else if (updated.status === 'failed') {
              anyChanges = true;
              return { ...job, status: `Background Error: ${updated.error}`, isError: true, completed: true };
            }
            allDone = false;
            return job;
          });
          return anyChanges ? { ...s, jobs: newJobs } : s;
        });

        // Check if any failed or succeeded, to re-show modal briefly if needed?
        // Let's just rely on the silent refresh for success, and maybe re-show on error.
        const newlyFailed = statuses.find(s => s.status === 'failed');
        if (newlyFailed) {
            setState(s => ({ ...s, visible: true }));
            await delay(4000);
            setState(s => ({ ...s, visible: false }));
        }

        if (statuses.some(s => s.status === 'completed')) {
             onSuccess?.(); // Silently refresh the list
        }

        activeJobIds = statuses.filter(s => s.status !== 'completed' && s.status !== 'failed').map(s => s.job_id);

        if (activeJobIds.length > 0) {
          setTimeout(poll, 2000);
        }

      } catch (err) {
        console.error("Polling error", err);
        setTimeout(poll, 2000); // Retry polling
      }
    };

    setTimeout(poll, 2000);

  }, [onSuccess]);

  return { overlayState: state, upload };
}

const delay = ms => new Promise(r => setTimeout(r, ms));
