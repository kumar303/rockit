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
                       .order_by('-created')[0:100])
    ob = []
    for afile in af.all():
        ob.append(afile.to_json())
    return {'songs': ob}
