"""
Enum for AI processing status.
"""
from enum import IntEnum


class AIStatus(IntEnum):
    """
    AI processing status codes for articles.
    
    Statusurile corespund cu valorile din baza de date:
    - 0: Neprocesate (not processed)
    - 1: În procesare (processing)
    - 2: Procesate (processed)
    - 9: Eroare (error)
    """
    NOT_PROCESSED = 0
    PROCESSING = 1
    PROCESSED = 2
    ERROR = 9
    
    @classmethod
    def to_string(cls, status: int) -> str:
        """Convert status code to human-readable string."""
        mapping = {
            cls.NOT_PROCESSED: "not_processed",
            cls.PROCESSING: "processing",
            cls.PROCESSED: "processed",
            cls.ERROR: "error"
        }
        return mapping.get(status, "unknown")
    
    @classmethod
    def from_string(cls, status_str: str) -> int:
        """Convert string to status code."""
        mapping = {
            "not_processed": cls.NOT_PROCESSED,
            "neprocesate": cls.NOT_PROCESSED,
            "processing": cls.PROCESSING,
            "in_procesare": cls.PROCESSING,
            "processed": cls.PROCESSED,
            "procesate": cls.PROCESSED,
            "error": cls.ERROR,
            "eroare": cls.ERROR
        }
        return mapping.get(status_str.lower(), cls.NOT_PROCESSED)
