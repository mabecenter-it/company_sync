from abc import ABC, abstractmethod

class ProgressObserver(ABC):
    @abstractmethod
    def update(self, percentage: float, context: dict):
        pass

    @abstractmethod
    def updateError(self, error_log: str, context: dict):
        pass
