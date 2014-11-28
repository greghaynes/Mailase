from mailase.tests.api import FunctionalTest


class TestRootController(FunctionalTest):

    def test_get_not_found(self):
        response = self.app.get('/a/bogus/url', expect_errors=True)
        assert response.status_int == 404

class TestMailboxController(FunctionalTest):

    def test_mailbox_index(self):
        response = self.app.get('/mailbox/')
        assert response.status_int == 200
