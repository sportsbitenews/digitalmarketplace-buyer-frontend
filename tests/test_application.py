from .helpers import BaseApplicationTest


class TestApplication(BaseApplicationTest):
    def test_index(self):
        response = self.client.get('/')
        assert 200 == response.status_code

    def test_404(self):
        response = self.client.get('/not-found')
        assert 404 == response.status_code

    def test_trailing_slashes(self):
        response = self.client.get('')
        assert 301 == response.status_code
        assert "http://localhost/" == response.location
        response = self.client.get('/trailing/')
        assert 301 == response.status_code
        assert "http://localhost/trailing" == response.location

    def test_trailing_slashes_with_query_parameters(self):
        response = self.client.get('/search/?q=r&s=t')
        assert 301 == response.status_code
        assert "http://localhost/search?q=r&s=t" == response.location
