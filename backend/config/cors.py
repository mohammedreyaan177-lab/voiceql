ALLOWED_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"

ALLOWED_HEADERS = "Accept, Content-Type, Origin, Authorization, X-Requested-With"


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = ALLOWED_METHODS
        response["Access-Control-Allow-Headers"] = ALLOWED_HEADERS
        response["Access-Control-Max-Age"] = "86400"

        return response
