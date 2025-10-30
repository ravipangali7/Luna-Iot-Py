from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from shared.models import ShortLink


@csrf_exempt
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
def resolve_short_link(request, code: str):
    try:
        sl = ShortLink.objects.get(code=code)
    except ShortLink.DoesNotExist:
        return Response({"detail": "Short link not found"}, status=status.HTTP_404_NOT_FOUND)
    if sl.expire_at and sl.expire_at < timezone.now():
        return Response({"detail": "Short link expired"}, status=status.HTTP_410_GONE)
    return Response({
        "code": sl.code,
        "url": sl.url,
        "expired": False,
        "usage_count": sl.usage_count,
    }, status=status.HTTP_200_OK)


