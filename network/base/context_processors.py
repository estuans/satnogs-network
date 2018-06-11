from django.conf import settings
from django.template.loader import render_to_string
from django.utils.timezone import now

from network.base.models import Observation


def analytics(request):
    """Returns analytics code."""
    if settings.ENVIRONMENT == 'production':
        return {'analytics_code': render_to_string('includes/analytics.html')}
    else:
        return {'analytics_code': ''}


def stage_notice(request):
    """Displays stage notice."""
    if settings.ENVIRONMENT == 'stage':
        return {'stage_notice': render_to_string('includes/stage_notice.html')}
    else:
        return {'stage_notice': ''}


def user_processor(request):
    if request.user.is_authenticated():
        owner_vetting_count = Observation.objects.filter(author=request.user,
                                                         vetted_status='unknown',
                                                         end__lt=now()).count()
        return {'owner_vetting_count': owner_vetting_count}
    else:
        return {'owner_vetting_count': ''}
