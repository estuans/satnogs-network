from django.core.exceptions import ObjectDoesNotExist


def schedule_perms(user, station=None):
    """
    This context flag will determine if user can schedule an observation.
    That includes station owners, moderators, admins.
    see: https://wiki.satnogs.org/Operation#Network_permissions_matrix
    """
    if user.is_authenticated():
        if station:
            if station.is_offline:
                return False
            if station.is_testing:
                if user.is_superuser:
                    return True
                if station not in user.ground_stations.all():
                    return False

        if user.ground_stations.exists():
            return True
        if user.groups.filter(name='Moderators').exists():
            return True
        if user.is_superuser:
            return True

    return False


def delete_perms(user, observation):
    """
    This context flag will determine if a delete button appears for the observation.
    That includes observer, station owner involved, moderators, admins.
    see: https://wiki.satnogs.org/Operation#Network_permissions_matrix
    """
    can_delete = False
    if user.is_authenticated():
        try:
            if observation.author == user:
                can_delete = True
        except AttributeError:
            pass
        try:
            if observation.ground_station.owner == user:
                can_delete = True
        except (AttributeError, ObjectDoesNotExist):
            pass
        if user.groups.filter(name='Moderators').exists():
            can_delete = True
        if user.is_superuser:
            can_delete = True
    return can_delete


def vet_perms(user, observation):
    """
    This context flag will determine if vet buttons appears for the observation.
    That includes observer, station owner involved, moderators, admins.
    see: https://wiki.satnogs.org/Operation#Network_permissions_matrix
    """
    can_vet = False
    if user.is_authenticated():
        try:
            if observation.author == user:
                can_vet = True
        except AttributeError:
            pass
        try:
            if observation.ground_station.owner == user:
                can_vet = True
        except AttributeError:
            pass
        if user.groups.filter(name='Moderators').exists():
            can_vet = True
        if user.is_superuser:
            can_vet = True
    return can_vet
