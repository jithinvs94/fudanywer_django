from . import models
from vendor import models as vend_model

def RequestObjectMiddleware(get_response):
    # One-time configuration and initialization.

    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        models.request_object = request
        vend_model.request_object = request

        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware