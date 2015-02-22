from testtools.matchers import Contains, Equals
from webtest.app import AppError

from mailase.tests.functional import base


class TestRootController(base.FunctionalTest):

    def test_get_not_found(self):
        response = self.app.get('/a/bogus/url', expect_errors=True)
        assert response.status_int == 404


class TestMailboxController(base.FunctionalTest):

    def test_index_without_trailing_slash(self):
        response = self.app.get('/mailbox')
        self.assertThat(response.status_int, Equals(302))
        self.assertThat(response.location, Equals('http://localhost/mailbox/'))

    def test_index_no_mailboxes(self):
        response = self.app.get('/mailbox/')
        self.assertThat(response.status_int, Equals(200))
        self.assertThat(response.json, Equals([]))

    def test_index_one_mailbox(self):
        self.useMailbox('INBOX')
        response = self.app.get('/mailbox/')
        self.assertThat(response.status_int, Equals(200))
        self.assertThat(response.json, Equals([{'id': 'INBOX'}]))

    def test_index_multi_mailbox(self):
        self.useMailbox('INBOX')
        self.useMailbox('SPAM')
        response = self.app.get('/mailbox/')
        self.assertThat(response.status_int, Equals(200))
        self.assertThat(response.json, Contains({'id': 'INBOX'}))
        self.assertThat(response.json, Contains({'id': 'SPAM'}))
        self.assertThat(len(response.json), Equals(2))

    def test_get_missing(self):
        self.assertRaises(AppError, self.app.get, '/mailbox/invalid')


class TestMailcontroller(base.FunctionalTest):

    def test_get_cur_hello_world(self):
        self.useMessage('helloworld', 'INBOX', 'cur')
        response = self.app.get('/mail/INBOX/helloworld:')
        msg = {u'from_': u'"Mailase Sender" <sender@mailase.test>',
               u'id': u'helloworld:',
               u'mailbox_id': u'INBOX',
               u'subject': u'Hello World!',
               u'text_payloads': [u'Hello, World!\n']}
        self.assertThat(response.json, Equals(msg))

    def test_get_missing_message(self):
        # Make sure dirs are made
        self.useMessage('helloworld', 'INBOX', 'cur')
        self.assertRaises(AppError, self.app.get, '/mail/INBOX/missing')
