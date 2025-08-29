from rest_framework.renderers import JSONRenderer
from collections.abc import Mapping

class EnvelopeJSONRenderer(JSONRenderer):
    """
    Ensures all successful responses are wrapped as:
    { "success": true, "data": ... }
    Handles paginated data and bare lists.
    Leaves already-enveloped responses unchanged.
    On errors, sets success=false and preserves details.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None
        status_code = getattr(response, 'status_code', 200)

        # If response is already an envelope with 'success', don't wrap again
        if isinstance(data, Mapping) and 'success' in data:
            return super().render(data, accepted_media_type, renderer_context)

        # Errors (4xx/5xx): wrap with success=false unless already wrapped
        if status_code >= 400:
            if isinstance(data, Mapping) and 'detail' in data:
                payload = {'success': False, 'message': data.get('detail')}
            else:
                payload = {'success': False, 'data': data}
            return super().render(payload, accepted_media_type, renderer_context)

        # Handle DRF pagination dict: {count,next,previous,results:[...]}
        if isinstance(data, Mapping) and 'results' in data:
            pagination = {
                'count': data.get('count'),
                'next': data.get('next'),
                'previous': data.get('previous'),
            }
            payload = {'success': True, 'data': data.get('results', []), 'pagination': pagination}
            return super().render(payload, accepted_media_type, renderer_context)

        # Bare list → wrap into data
        if isinstance(data, list):
            payload = {'success': True, 'data': data}
            return super().render(payload, accepted_media_type, renderer_context)

        # Any other dict without 'success' → wrap into data
        if isinstance(data, Mapping):
            payload = {'success': True, 'data': data}
            return super().render(payload, accepted_media_type, renderer_context)

        # Fallback: wrap as-is
        payload = {'success': True, 'data': data}
        return super().render(payload, accepted_media_type, renderer_context)