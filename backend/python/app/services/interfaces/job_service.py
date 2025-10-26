from abc import ABC, abstractmethod

from app.models.job import Job


class IJobService(ABC):
    @abstractmethod
    def get_jobs(self) -> list[Job]:
        """Return a list of all jobs, optionally filtered by progress.
        :param progress: Optional progress status to filter jobs
        :type progress: ProgressEnum, optional
        :return: A list of Job objects
        :rtype: list[Job]
        :raises Exception: if job fields are invalid
        """
        pass
