"""
Background Job Manager for handling long-running tasks
Supports in-memory storage with optional JSON persistence
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import json
from pathlib import Path
import threading


class JobManager:
    """Simple job manager with in-memory storage and optional persistence"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        self._lock = threading.Lock()
        
        # Load existing jobs if storage path provided
        if self.storage_path and self.storage_path.exists():
            self._load_jobs()
    
    def _load_jobs(self):
        """Load jobs from JSON file"""
        try:
            with open(self.storage_path, 'r') as f:
                self.jobs = json.load(f)
        except Exception as e:
            print(f"Failed to load jobs: {e}")
    
    def _save_jobs(self):
        """Save jobs to JSON file"""
        if not self.storage_path:
            return
        
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.jobs, f, indent=2)
        except Exception as e:
            print(f"Failed to save jobs: {e}")
    
    def create_job(self, job_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new job and return job ID"""
        with self._lock:
            job_id = str(uuid.uuid4())
            self.jobs[job_id] = {
                "id": job_id,
                "type": job_type,
                "status": "pending",  # pending, running, completed, failed
                "progress": 0,
                "total": 0,
                "current_step": "",
                "result": None,
                "error": None,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None
            }
            self._save_jobs()
            return job_id
    
    def update_job(self, job_id: str, **kwargs):
        """Update job with new data"""
        with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id].update(kwargs)
                self.jobs[job_id]["updated_at"] = datetime.now().isoformat()
                
                # Set timestamps based on status
                if kwargs.get("status") == "running" and not self.jobs[job_id].get("started_at"):
                    self.jobs[job_id]["started_at"] = datetime.now().isoformat()
                elif kwargs.get("status") in ["completed", "failed"]:
                    self.jobs[job_id]["completed_at"] = datetime.now().isoformat()
                
                self._save_jobs()
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        with self._lock:
            return self.jobs.get(job_id)
    
    def get_all_jobs(self, job_type: Optional[str] = None, limit: int = 50) -> list:
        """Get all jobs, optionally filtered by type"""
        with self._lock:
            jobs = list(self.jobs.values())
            
            if job_type:
                jobs = [j for j in jobs if j["type"] == job_type]
            
            # Sort by created_at descending
            jobs.sort(key=lambda x: x["created_at"], reverse=True)
            
            return jobs[:limit]
    
    def delete_job(self, job_id: str):
        """Delete a job"""
        with self._lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                self._save_jobs()
    
    def cleanup_old_jobs(self, days: int = 7):
        """Delete jobs older than specified days"""
        from datetime import timedelta
        
        with self._lock:
            cutoff = datetime.now() - timedelta(days=days)
            jobs_to_delete = []
            
            for job_id, job in self.jobs.items():
                created = datetime.fromisoformat(job["created_at"])
                if created < cutoff and job["status"] in ["completed", "failed"]:
                    jobs_to_delete.append(job_id)
            
            for job_id in jobs_to_delete:
                del self.jobs[job_id]
            
            if jobs_to_delete:
                self._save_jobs()
            
            return len(jobs_to_delete)


# Global instance
job_manager = JobManager(storage_path="./jobs.json")
