from fixtures import MonkeyPatch
from testtools.matchers import Contains, Equals
from webtest.app import AppError

from mailase.tests.functional import base


class TestRootController(base.FunctionalTest):
    def test_get_not_found(self):
        response = self.app.get('/a/bogus/url', expect_errors=True)
        assert response.status_int == 404


class TestMailboxController(base.FunctionalTest):
    def test_index_without_trailing_slash(self):
        response = self.app.get('/mailboxes')
        self.assertThat(response.status_int, Equals(302))
        self.assertThat(response.location,
                        Equals('http://localhost/mailboxes/'))

    def test_index_no_mailboxes(self):
        response = self.app.get('/mailboxes/')
        self.assertThat(response.status_int, Equals(200))
        self.assertThat(response.json, Equals([]))

    def test_index_one_mailbox(self):
        self.useMailbox('INBOX')
        response = self.app.get('/mailboxes/')
        self.assertThat(response.status_int, Equals(200))
        self.assertThat(response.json, Equals([{'id': 'INBOX',
                                                'mail_briefs': []}]))

    def test_index_multi_mailbox(self):
        self.useMailbox('INBOX')
        self.useMailbox('SPAM')
        response = self.app.get('/mailboxes/')
        self.assertThat(response.status_int, Equals(200))
        self.assertThat(response.json,
                        Contains({'id': 'INBOX',
                                  'mail_briefs': []}))
        self.assertThat(response.json,
                        Contains({'id': 'SPAM',
                                  'mail_briefs': []}))
        self.assertThat(len(response.json), Equals(2))

    def test_mailbox_invalid_index(self):
        self.assertRaises(AppError, self.app.get, '/mailboxes/invalid')


class TestMailcontroller(base.FunctionalTest):
    def setUp(self):
        super(TestMailcontroller, self).setUp()

        def fake_getmtime(path):
            return 12456.7
        self.useFixture(MonkeyPatch('os.path.getmtime', fake_getmtime))

    def test_get_message_cur_hello_world(self):
        self.useMessage('helloworld', 'INBOX', 'cur')
        response = self.app.get('/mail/INBOX/helloworld:')
        msg = {'brief': {'id' : 'helloworld:',
                         'mailbox_id': 'INBOX',
                         'modified_on': 12456,
                         'receiver': '"Mailase Receiver" <receiver@mailase.test>',
                         'sender': '"Mailase Sender" <sender@mailase.test>',
                         'subdir': 'cur',
                         'subject': 'Hello World!'},
               'text_payloads': ['Hello, World!\n']}
        self.assertThat(response.json, Equals(msg))

    def test_get_message_new_hello_world(self):
        self.useMessage('helloworld', 'INBOX', 'new')
        response = self.app.get('/mail/INBOX/helloworld:')
        msg = {'brief': {'id': 'helloworld:',
                         'mailbox_id': 'INBOX',
                         'modified_on': 12456,
                         'receiver': '"Mailase Receiver" <receiver@mailase.test>',
                         'sender': '"Mailase Sender" <sender@mailase.test>',
                         'subdir': 'new',
                         'subject': 'Hello World!'},
               'text_payloads': ['Hello, World!\n']}
        self.assertThat(response.json, Equals(msg))

    def test_get_invalid_message(self):
        # Make sure dirs are made
        self.useMessage('helloworld', 'INBOX', 'cur')
        self.assertRaises(AppError, self.app.get, '/mail/INBOX/missing')

    def test_get_message_invalid_mailbox(self):
        self.assertRaises(AppError, self.app.get, '/mail/INBOX/missing')
