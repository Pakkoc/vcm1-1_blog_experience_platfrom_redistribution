"""
Custom exception classes for service layer.
"""


class ServiceException(Exception):
    """
    Base exception for service layer business logic errors.

    Use this for general business logic validation failures.
    """
    pass


class PermissionDeniedException(ServiceException):
    """
    Exception raised when user lacks required permissions.

    Example:
        - Influencer trying to create a campaign
        - User trying to modify another user's data
    """
    pass


class InvalidStateException(ServiceException):
    """
    Exception raised when attempting an invalid state transition.

    Example:
        - Applying to a closed campaign
        - Selecting more influencers than recruitment count
        - Modifying a completed campaign
    """
    pass


class DuplicateActionException(ServiceException):
    """
    Exception raised when attempting a duplicate action.

    Example:
        - Applying to the same campaign twice
        - Creating duplicate profile
    """
    pass


class ValidationException(ServiceException):
    """
    Exception raised when data validation fails.

    Example:
        - Invalid date range (start_date > end_date)
        - Missing required fields
        - Business rule violations
    """
    pass
