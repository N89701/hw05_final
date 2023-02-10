from django.conf import settings
from django.core.paginator import Paginator


def paginator(request, objects):
    paginator = Paginator(objects, settings.PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
