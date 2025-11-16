"""
Base Service class for business logic.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

InputDTO = TypeVar('InputDTO')
OutputType = TypeVar('OutputType')


class BaseService(ABC, Generic[InputDTO, OutputType]):
    """
    Base class for all service classes.

    Services encapsulate business logic and follow the command pattern.
    They receive a DTO as input and return a result (model instance or DTO).
    """

    @abstractmethod
    def execute(self, dto: InputDTO, user: Optional[object] = None) -> OutputType:
        """
        Execute the business logic.

        Args:
            dto: Input data transfer object
            user: Current request user (optional)

        Returns:
            Execution result (model instance or DTO)

        Raises:
            ServiceException: When business logic validation fails
        """
        pass
