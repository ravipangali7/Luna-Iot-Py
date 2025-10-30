from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.utils import timezone
from shared.models import ShortLink


def redirect_short_link(request, code: str):
    try:
        sl = ShortLink.objects.get(code=code)
        if sl.expire_at and sl.expire_at < timezone.now():
            return HttpResponseNotFound("Link expired")
        sl.usage_count = sl.usage_count + 1
        sl.save(update_fields=["usage_count"])
        return HttpResponseRedirect(sl.url)
    except ShortLink.DoesNotExist:
        return HttpResponseNotFound("Link not found")


