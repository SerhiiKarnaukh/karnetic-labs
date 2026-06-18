from core.models import TopbarLink


def get_active_topbar_links():
    return TopbarLink.objects.exclude(url='').order_by('ordering', 'key')
