from django.views.generic import TemplateView

from rest_framework.utils.urls import remove_query_param, replace_query_param
from rest_framework.pagination import _get_displayed_page_numbers, _get_page_links


def get_page_links(request, page, page_query_param='page'):

    base_url = request.build_absolute_uri()

    def page_number_to_url(page_number):
        if page_number == 1:
            return remove_query_param(base_url, page_query_param)
        else:
            return replace_query_param(base_url, page_query_param, page_number)

    current = page.number
    final = page.paginator.num_pages
    page_numbers = _get_displayed_page_numbers(current, final)
    return _get_page_links(page_numbers, current, page_number_to_url)


class IndexView(TemplateView):

    template_name = 'index.html'


