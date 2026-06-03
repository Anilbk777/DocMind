import threading
from typing import Dict, Any, Optional


class JobTracker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(JobTracker, cls).__new__(cls)
                cls._instance.jobs: Dict[str, Dict[str, Any]] = {}
        return cls._instance

    def create_job(self, job_id: str, filename: str, batch_id: str) -> None:
        """Initialize a new job with 'processing' status."""
        self.jobs[job_id] = {
            "job_id": job_id,
            "filename": filename,
            "batch_id": batch_id,
            "status": "processing",
            "error": None,
            "saved_path": None,
            "chunks_created": 0,
        }

    def update_job_success(
        self, job_id: str, saved_path: str, chunks_created: int
    ) -> None:
        """Mark job as completed successfully."""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "completed"
            self.jobs[job_id]["saved_path"] = saved_path
            self.jobs[job_id]["chunks_created"] = chunks_created

    def update_job_error(self, job_id: str, error_msg: str) -> None:
        """Mark job as failed with an error message."""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = error_msg

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve job status."""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Retrieve all jobs."""
        return self.jobs

    def get_batch_jobs(self, batch_id: str) -> list[dict]:
        return [job for job in self.jobs.values() if job["batch_id"] == batch_id]



