from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.exception_utils import handle_api_exception

from shared.models import ExternalAppLink


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_external_app_links(request):
    """
    Get all external app links
    """
    try:
        external_app_links = ExternalAppLink.objects.all().order_by('name')
        
        links_data = []
        for link in external_app_links:
            link_data = {
                'id': link.id,
                'name': link.name,
                'link': link.link,
                'username': link.username,
                'password': link.password,
                'logo': link.logo or '',
                'createdAt': link.createdAt.isoformat() if link.createdAt else None,
                'updatedAt': link.updatedAt.isoformat() if link.updatedAt else None
            }
            links_data.append(link_data)
        
        return success_response(links_data, 'External app links retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)

