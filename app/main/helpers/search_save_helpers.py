from urllib.parse import urlencode, urlunparse, urlparse
from werkzeug.datastructures import MultiDict
from flask import url_for

from app.main.helpers.framework_helpers import get_latest_live_framework, get_lots_by_slug

from app.main.presenters.search_presenters import filters_for_lot
from app.main.presenters.search_summary import SearchSummary
from app.main.helpers.search_helpers import clean_request_args

from app import search_api_client, data_api_client, content_loader


class SearchMeta(object):
    def __init__(self, search_api_url, all_frameworks):
        # Get core data
        framework = get_latest_live_framework(all_frameworks, 'g-cloud')
        content_manifest = content_loader.get_manifest(framework['slug'], 'search_filters')
        lots_by_slug = get_lots_by_slug(framework)

         # We need to get buyer-frontend query params from our saved search API URL.
        search_query_params = search_api_client.get_frontend_params_from_search_api_url(search_api_url)
        search_query_params_multidict = MultiDict(search_query_params)

        current_lot_slug = search_query_params_multidict.get('lot', None)
        filters = filters_for_lot(current_lot_slug, content_manifest, all_lots=framework['lots'])
        clean_request_query_params = clean_request_args(search_query_params_multidict, filters.values(), lots_by_slug)

        # Now build the buyer-frontend URL representing the saved Search API URL
        search_page_base_url = url_for('main.search_services')
        parsed_url = list(urlparse(search_page_base_url))
        parsed_url[4] = urlencode(search_query_params)
        self.url = urlunparse(parsed_url)

        # Get the saved Search API URL result set and build the search summary.
        search_api_response = search_api_client._get(search_api_url)
        self.search_summary = SearchSummary(
            search_api_response['meta']['total'],
            clean_request_query_params.copy(),
            filters.values(),
            lots_by_slug
        )
