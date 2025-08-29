from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse

class AppendSlashAPIMiddleware(MiddlewareMixin):
    def process_request(self, request):
        path = request.path
        # Only adjust API endpoints; skip if already endswith /, static files, or admin
        if not path.startswith('/api/'):
            return None
        if path.endswith('/'):
            return None
        # Avoid appending slash to file-like paths (e.g. .json, .png)
        if '.' in path.rsplit('/', 1)[-1]:
            return None

        # Build target with slash and preserve query string
        target = path + '/'
        if request.META.get('QUERY_STRING'):
            target = f"{target}?{request.META['QUERY_STRING']}"

        # 307 keeps method and body intact
        response = HttpResponse(status=307)
        response['Location'] = target
        return response