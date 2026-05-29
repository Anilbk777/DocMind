import { useState, useCallback } from 'react';
import { uploadDocument, getJobStatus } from '../services/api';

export function useUpload(onSuccess) {
  const [state, setState] = useState({ visible: false, filename: '', status: '', isError: false });

  const upload = useCallback(async (file) => {
    setState({ visible: true, filename: file.name, status: 'Uploading...', isError: false });
    try {
      const uploadRes = await uploadDocument(file);
      const jobId = uploadRes.job_id;

      setState(s => ({ ...s, status: 'Upload complete! Processing in background...' }));

      // Close the modal shortly after upload succeeds, so user can do other things
      await delay(1500);
      setState(s => ({ ...s, visible: false }));

      const poll = async () => {
        try {
          const job = await getJobStatus(jobId);
          if (job.status === 'completed') {
            // Silently refresh the list when done
            onSuccess?.();
          } else if (job.status === 'failed') {
            setState({ visible: true, filename: file.name, status: `Background Error: ${job.error}`, isError: true });
            await delay(4000);
            setState(s => ({ ...s, visible: false }));
          } else {
            // Still processing
            setTimeout(poll, 2000);
          }
        } catch (err) {
            setState({ visible: true, filename: file.name, status: `Polling Error: ${err.message}`, isError: true });
            await delay(3000);
            setState(s => ({ ...s, visible: false }));
        }
      };

      setTimeout(poll, 2000);

    } catch (err) {
      setState(s => ({ ...s, status: `Error: ${err.message}`, isError: true }));
      await delay(3000);
      setState(s => ({ ...s, visible: false }));
    }
  }, [onSuccess]);

  return { overlayState: state, upload };
}

const delay = ms => new Promise(r => setTimeout(r, ms));
