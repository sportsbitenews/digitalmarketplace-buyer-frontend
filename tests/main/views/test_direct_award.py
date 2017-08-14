from lxml import html
import mock

from app import data_api_client
from dmutils.formats import utcdatetimeformat
from ..helpers.test_search_helpers import find_search_summary
from ...helpers import BaseApplicationTest


class TestDirectAward(BaseApplicationTest):
    def setup_method(self, method):
        super(TestDirectAward, self).setup_method(method)

        self._search_api_client_patch = mock.patch('app.main.views.g_cloud.search_api_client', autospec=True)
        self._search_api_client = self._search_api_client_patch.start()

        self._search_api_client_presenters_patch = mock.patch('app.main.presenters.search_presenters.search_api_client',
                                                              autospec=True)
        self._search_api_client_presenters = self._search_api_client_presenters_patch.start()
        self._search_api_client_presenters.aggregate_services.return_value = \
            self._get_fixture_data('g9_aggregations_fixture.json')

        self.g9_search_results = self._get_g9_search_results_fixture_data()
        self.search_results_multiple_page = self._get_search_results_multiple_page_fixture_data()

        data_api_client.get_direct_award_project = mock.Mock()
        data_api_client.get_direct_award_project.return_value = self._get_direct_award_project_fixture()

        data_api_client.find_direct_award_project_searches = mock.Mock()
        data_api_client.find_direct_award_project_searches.return_value = \
            self._get_direct_award_project_searches_fixture()

    def teardown_method(self, method):
        self._search_api_client_patch.stop()
        self._search_api_client_presenters_patch.stop()

    def test_renders_save_search_button(self):
        self._search_api_client.search_services.return_value = self.g9_search_results

        res = self.client.get('/g-cloud/search')
        assert res.status_code == 200

        doc = html.fromstring(res.get_data(as_text=True))
        assert len(doc.xpath('//button[@id="save-search" and @formaction="/buyers/direct-award/save-search"]')) == 1

    def test_save_search_redirects_to_login(self):
        self._search_api_client.search_services.return_value = self.search_results_multiple_page

        res = self.client.get('/buyers/direct-award/save-search?lot=cloud-software')
        assert res.status_code == 302

    def test_save_search_renders_summary_on_page(self):
        self.login_as_buyer()

        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get('/buyers/direct-award/save-search?lot=cloud-software')
        assert res.status_code == 200

        summary = find_search_summary(res.get_data(as_text=True))[0]
        assert '<span class="search-summary-count">1</span> result found in <em>Cloud software</em>' in summary

    def test_view_project_page_shows_title(self):
        self.login_as_buyer()

        res = self.client.get('/buyers/direct-award/projects/1')

        doc = html.fromstring(res.get_data(as_text=True))
        project_name = self._get_direct_award_project_fixture()['project']['name']
        assert len(doc.xpath('//h1[contains(normalize-space(text()), "Project - {}")]'.format(project_name))) == 1

    def test_view_project_shows_active_search_details(self):
        self._search_api_client.deconstruct_url.return_value = (('q', 'accelerator'), )
        self.login_as_buyer()

        return_value = self.search_results_multiple_page
        return_value["services"] = [return_value["services"][0]]
        return_value["meta"]["total"] = 1
        self._search_api_client.search_services.return_value = return_value

        res = self.client.get('/buyers/direct-award/projects/1')
        assert res.status_code == 200

        body = res.get_data(as_text=True)
        doc = html.fromstring(body)
        summary = find_search_summary(body)[0]
        assert '<span class="search-summary-count">1</span> result found containing <em>accelerator</em> in ' \
               '<em>All categories</em>' in summary
        assert utcdatetimeformat(self._get_direct_award_project_searches_fixture()['searches'][0]['createdAt']) in body
        assert len(doc.xpath('//a[@href="/g-cloud/search?q=accelerator"]')) == 1
