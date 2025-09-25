from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    message = "An unexpected error occurred."

    # Handle DRF validation errors (serializer / field validation)
    if isinstance(exc, ValidationError):
        # DRF packs errors like {"email": ["This field is required."]}
        # or {"non_field_errors": ["Invalid credentials"]}
        errors = []
        for field, msgs in exc.detail.items():
            if isinstance(msgs, list):
                errors.extend(msgs)
            else:
                errors.append(str(msgs))
        message = errors[0] if errors else "Validation error."

        return Response({
            "success": False,
            "message": message,
            "requires_verification": False
        }, status=status.HTTP_400_BAD_REQUEST)

    # Handle DB integrity errors (duplicate email/phone)
    if isinstance(exc, IntegrityError):
        if "account.email" in str(exc).lower():
            message = "An account with this email already exists."
        elif "account.phone" in str(exc).lower():
            message = "An account with this phone number already exists."
        else:
            message = "Duplicate entry detected."

        return Response({
            "success": False,
            "message": message,
            "requires_verification": False
        }, status=status.HTTP_400_BAD_REQUEST)

    # For all other errors (fallback)
    if response is not None:
        return Response({
            "success": False,
            "message": str(exc),
            "requires_verification": False
        }, status=response.status_code)

    return Response({
        "success": False,
        "message": message,
        "requires_verification": False
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
