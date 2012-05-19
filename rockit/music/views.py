from django.shortcuts import get_object_or_404

from rockit.sync.decorators import json_view
from .decorators import require_api_key
from .models import VerifiedEmail, Track


@json_view
@require_api_key
def index(request, raw_sig_request, sig_request):
    email = get_object_or_404(VerifiedEmail,
                              email=sig_request['request']['email'])
    af = (Track.objects.filter(email=email)
                       .exclude(files=None)
                       .order_by('-created'))
    default_offset = 0
    default_size = 50
    max_size = 100
    page_size = sig_request['request'].get('page_size', default_size)
    page_size = make_int(page_size, default_size)
    if page_size > max_size:
        page_size = max_size
    offset = sig_request['request'].get('offset', default_offset)
    offset = make_int(offset, default_offset)
    af = af[offset: offset + page_size]

    ob = []
    for afile in af.all():
        ob.append(afile.to_json())
    return {'tracks': ob}


def make_int(val, default):
    try:
        return int(val)
    except ValueError:
        return default
