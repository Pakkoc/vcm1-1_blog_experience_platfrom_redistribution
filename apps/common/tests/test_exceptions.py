"""
Test cases for custom exceptions.
"""

import pytest
from apps.common.exceptions import (
    ServiceException,
    PermissionDeniedException,
    InvalidStateException,
    DuplicateActionException,
    ValidationException
)


class TestServiceExceptions:
    """Test cases for service layer exceptions"""

    def test_service_exception_is_raised(self):
        """ServiceException should be raised and caught"""
        with pytest.raises(ServiceException):
            raise ServiceException("Test error")

    def test_permission_denied_exception_inherits_service_exception(self):
        """PermissionDeniedException should inherit from ServiceException"""
        assert issubclass(PermissionDeniedException, ServiceException)

        with pytest.raises(ServiceException):
            raise PermissionDeniedException("No permission")

    def test_invalid_state_exception_inherits_service_exception(self):
        """InvalidStateException should inherit from ServiceException"""
        assert issubclass(InvalidStateException, ServiceException)

        with pytest.raises(ServiceException):
            raise InvalidStateException("Invalid state")

    def test_duplicate_action_exception_inherits_service_exception(self):
        """DuplicateActionException should inherit from ServiceException"""
        assert issubclass(DuplicateActionException, ServiceException)

        with pytest.raises(ServiceException):
            raise DuplicateActionException("Duplicate action")

    def test_validation_exception_inherits_service_exception(self):
        """ValidationException should inherit from ServiceException"""
        assert issubclass(ValidationException, ServiceException)

        with pytest.raises(ServiceException):
            raise ValidationException("Validation failed")

    def test_exception_message_is_preserved(self):
        """Exception message should be preserved"""
        message = "Test error message"
        with pytest.raises(ServiceException) as exc_info:
            raise ServiceException(message)

        assert str(exc_info.value) == message
