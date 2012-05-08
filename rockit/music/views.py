from django.shortcuts import get_object_or_404

from rockit.sync.decorators import json_view
from .decorators import require_api_key
from .models import VerifiedEmail, AudioFile


@json_view
@require_api_key
def index(request, raw_sig_request, sig_request):
    email = get_object_or_404(VerifiedEmail,
                              email=sig_request['request']['email'])
    af = (AudioFile.objects.filter(email=email)
                           .exclude(s3_ogg_url=None)
                           .order_by('-created'))
    ob = []
    for afile in af.all():
        ob.append(afile.to_json())
    return {'songs': ob}
