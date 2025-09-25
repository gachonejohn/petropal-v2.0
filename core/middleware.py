from django.utils.deprecation import MiddlewareMixin
from rest_framework.response import Response

class CustomResponseMiddleware(MiddlewareMixin):
    """
    Wrap all DRF success responses in a consistent format
    unless the view already returns in the correct format.
    """

    def process_template_response(self, request, response):
        return response

    def process_response(self, request, response):
        if isinstance(response, Response):
            # Only wrap success responses (2xx codes)
            if 200 <= response.status_code < 300:
                if isinstance(response.data, dict):
                    # Don't re-wrap if it's already using your format
                    if "message" in response.data and ("acc_id" in response.data or "success" in response.data):
                        return response

                    # Wrap in your custom format
                    response.data = {
                        "success": True,
                        "data": response.data,
                        "message": "Request processed successfully.",
                        "requires_verification": response.data.get("requires_verification", False)
                    }
        return response
