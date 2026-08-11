from enum import Enum


class JobType(str, Enum):
    TRANSCODE = "transcode"
    THUMBNAIL = "thumbnail"
    AUDIO_EXTRACT = "audio_extract"
    METADATA = "metadata"


class JobStatus(str, Enum):
    """Job lifecycle state machine.

    PENDING    -> QUEUED     (accepted, pushed onto the Redis queue)
    QUEUED     -> PROCESSING (a worker claimed the job)
    PROCESSING -> COMPLETED  (success)
    PROCESSING -> RETRYING   (failed, retries remain; scheduled for later)
    RETRYING   -> QUEUED     (backoff elapsed, promoted back onto the queue)
    PROCESSING -> FAILED     (failed, retries exhausted -> dead letter)
    QUEUED/PENDING -> CANCELLED (operator cancelled before it ran)
    PROCESSING -> QUEUED     (heartbeat timeout / worker crash -> reaped)
    """

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def terminal(cls) -> set["JobStatus"]:
        return {cls.COMPLETED, cls.FAILED, cls.CANCELLED}


class WorkerStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


# Priority is a plain integer (0-10). These named levels are provided for
# convenience/documentation and used by the frontend job creation form.
class JobPriority(int, Enum):
    LOW = 2
    NORMAL = 5
    HIGH = 8
    URGENT = 10
