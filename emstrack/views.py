import math
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


def get_page_size_links(request, page, page_sizes, page_query_param='page', page_size_query_param='page_size'):

    base_url = request.build_absolute_uri()

    def page_size_to_url(page_size, page_number):

        # remove query params
        url = remove_query_param(base_url, page_query_param)
        url = remove_query_param(url, page_size_query_param)

        # process page number
        if page_number > 1:
            url = replace_query_param(base_url, page_query_param, page_number)

        # process page size
        return replace_query_param(url, page_size_query_param, page_size)

    start_index = page.start_index()
    return [{'url': page_size_to_url(page_size, page_number), 'size': page_size}
            for page_size, page_number in [(size, math.floor(start_index / size)) for size in page_sizes]]


class IndexView(TemplateView):

    template_name = 'index.html'


