from django.shortcuts import redirect
from django.core.urlresolvers import reverse


def admin_required(function):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect(reverse('account_login'))
        if request.user.is_superuser:
            return function(request, *args, **kwargs)
        else:
            return redirect(reverse('base:home'))
    return wrap
