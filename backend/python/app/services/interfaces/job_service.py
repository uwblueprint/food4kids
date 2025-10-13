from abc import ABC, abstractmethod

from app.models.job import Job


class IJobService(ABC):
    @abstractmethod
    def get_jobs(self) -> list[Job]:
        pass
