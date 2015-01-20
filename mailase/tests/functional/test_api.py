from mailase.tests.functional import base


class TestRootController(base.FunctionalTest):

    def test_get_not_found(self):
        response = self.app.get('/a/bogus/url', expect_errors=True)
        assert response.status_int == 404


class TestMailboxController(base.FunctionalTest):

    def test_mailbox_index(self):
        response = self.app.get('/mailbox/')
        assert response.status_int == 200
