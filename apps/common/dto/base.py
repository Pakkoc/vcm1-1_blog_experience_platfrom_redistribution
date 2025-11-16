"""
Base Data Transfer Object (DTO) class.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BaseDTO:
    """
    Base class for all DTOs.

    - frozen=True ensures immutability
    - Use dataclass features for automatic __init__, __repr__, etc.
    """
    pass
