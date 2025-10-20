from rest_framework.pagination import PageNumberPagination

class FeaturedUsersPagination(PageNumberPagination):
    page_size = 5  
    page_size_query_param = 'page_size'  # allow client to override if needed
    max_page_size = 20
