import logging
from collections.abc import Mapping

from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ErrorDetail, PermissionDenied, Throttled, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core import constants

logger = logging.getLogger(__name__)


class BusinessAPIException(APIException):
    extra_data = None

    def __init__(self, detail=None, code=None, extra_data=None):
        super().__init__(detail=detail or self.default_detail, code=code or self.default_code)
        self.extra_data = extra_data or {}


class ResourceNotFoundException(BusinessAPIException):
    status_code = 404
    default_detail = "Resource not found."
    default_code = constants.ERROR_RESOURCE_NOT_FOUND


class DuplicateResourceException(BusinessAPIException):
    status_code = 409
    default_detail = "Duplicate resource."
    default_code = constants.ERROR_DUPLICATE_RESOURCE


class InsufficientInventoryException(BusinessAPIException):
    status_code = 422
    default_detail = "Insufficient inventory."
    default_code = constants.ERROR_INSUFFICIENT_INVENTORY


class InvalidOperationException(BusinessAPIException):
    status_code = 422
    default_detail = "Invalid operation."
    default_code = constants.ERROR_INVALID_OPERATION


class BusinessPermissionException(BusinessAPIException):
    status_code = 403
    default_detail = "Permission denied."
    default_code = constants.ERROR_PERMISSION_DENIED


def _timestamp():
    return timezone.now().isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _stringify(value):
    if isinstance(value, ErrorDetail):
        return str(value)
    if isinstance(value, list):
        return " ".join(_stringify(item) for item in value)
    if isinstance(value, Mapping):
        return " ".join(_stringify(item) for item in value.values())
    return str(value)


def _flatten_errors(detail, prefix=""):
    errors = []
    if isinstance(detail, Mapping):
        for field, value in detail.items():
            next_prefix = f"{prefix}.{field}" if prefix else str(field)
            errors.extend(_flatten_errors(value, next_prefix))
    elif isinstance(detail, list):
        for item in detail:
            if isinstance(item, (Mapping, list)):
                errors.extend(_flatten_errors(item, prefix))
            else:
                errors.append({"field": prefix or "non_field_errors", "message": _stringify(item)})
    else:
        errors.append({"field": prefix or "non_field_errors", "message": _stringify(detail)})
    return errors


def _error_code(exc, response, request):
    if isinstance(exc, ValidationError):
        return constants.ERROR_VALIDATION_FAILED
    if isinstance(exc, Throttled) and request and request.path == constants.LOGIN_PATH:
        return constants.ERROR_TOO_MANY_LOGIN_ATTEMPTS
    if response is not None and response.status_code == status.HTTP_401_UNAUTHORIZED:
        return constants.ERROR_NOT_AUTHENTICATED
    if isinstance(exc, PermissionDenied):
        code = exc.get_codes()
        return code if isinstance(code, str) and code != "permission_denied" else constants.ERROR_PERMISSION_DENIED
    if isinstance(exc, APIException):
        code = exc.get_codes()
        if isinstance(code, str):
            return code.upper()
    return constants.ERROR_INTERNAL_SERVER_ERROR


def _message(exc, response):
    if response is None:
        return "Internal server error."
    detail = getattr(exc, "detail", None)
    if isinstance(detail, Mapping):
        if "detail" in detail:
            return _stringify(detail["detail"])
        return _stringify(detail)
    if isinstance(detail, list):
        return _stringify(detail)
    return _stringify(detail) if detail is not None else str(exc)


def custom_exception_handler(exc, context):
    request = context.get("request")
    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled API exception", exc_info=exc)
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        status_code = response.status_code

    errors = _flatten_errors(exc.detail) if isinstance(exc, ValidationError) else []
    data = {
        "timestamp": _timestamp(),
        "status": status_code,
        "error_code": _error_code(exc, response, request),
        "message": _message(exc, response),
        "path": request.path if request else "",
        "errors": errors,
    }
    data.update(getattr(exc, "extra_data", {}) or {})
    return Response(data, status=status_code)

