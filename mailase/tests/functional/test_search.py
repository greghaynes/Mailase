import elasticsearch
from fixtures import Fixture
from pecan import conf
from testtools.matchers import Equals

from mailase.api.model import Mail
import mailase.search.dbapi as search_api
from mailase.search.indexer import Indexer
from mailase.tests.functional import base


class EsIndexFixture(Fixture):
    def __init__(self, index):
        super(EsIndexFixture, self).__init__()
        self.index = index

    def setUp(self):
        super(EsIndexFixture, self).setUp()
        create_body = {'index': {'store': {'type': 'memory'}}}
        try:
            search_api.refresh()
        except elasticsearch.TransportError as e:
            pass

        try:
            search_api.es_client.indices.create(index=self.index,
                                                body=create_body)
        except elasticsearch.TransportError as e:
            if e.status_code == 400:
                search_api.es_client.indices.delete(index=self.index)
                search_api.es_client.indices.create(index=self.index,
                                                    body=create_body)
            else:
                raise
        search_api.refresh()
        if not search_api.es_client.indices.exists(index=self.index):
            raise Exception("Index does not exist!")

    def cleanUp(self):
        super(EsIndexFixture, self).cleanUp()
        search_api.es_client.indices.delete(index=self.index)


class IndexerFixture(Fixture):
    def __init__(self):
        super(IndexerFixture, self).__init__()
        self.indexer = Indexer(conf.mail.maildirs)

    def cleanUp(self):
        self.indexer.stop()
        self.indexer.join()
        del self.indexer


class TestSearch(base.FunctionalTest):
    def setUp(self):
        super(TestSearch, self).setUp()
        self.useFixture(EsIndexFixture(conf.search.index))
        indexer_fixture = IndexerFixture()
        self.useFixture(indexer_fixture)
        self.indexer = indexer_fixture.indexer

    def test_is_alive(self):
        res = self.app.get('/search/')
        self.assertThat(res.json, Equals(True))

    def test_empty_recent_index_defaults(self):
        res = self.app.get('/search/recent/')
        self.assertThat(res.json,
                        Equals({'mail_briefs': [],
                                'limit': 100,
                                'offset': 0}))

    def test_empty_recent_index_limit_offset(self):
        res = self.app.get('/search/recent/?offset=5&limit=1')
        self.assertThat(res.json,
                        Equals({'mail_briefs': [],
                                'limit': 1,
                                'offset': 5}))

    def test_recent_index_single_message_cur(self):
        self.useMessage('helloworld', 'INBOX', 'cur')
        self.indexer.reindex()
        search_api.refresh()
        res = self.app.get('/search/recent/')
        self.assertThat(len(res.json['mail_briefs']), Equals(1))

    def test_recent_index_multiple_message_new(self):
        self.useMessage('helloworld', 'INBOX', 'new')
        self.useMessage('helloworld_2', 'INBOX', 'new')
        self.indexer.reindex()
        search_api.refresh()
        res = self.app.get('/search/recent/')
        self.assertThat(len(res.json['mail_briefs']), Equals(2))

    def test_recent_index_multiple_message_cur_new(self):
        self.useMessage('helloworld', 'INBOX', 'new')
        self.useMessage('helloworld_2', 'INBOX', 'new')
        self.indexer.reindex()
        search_api.refresh()
        res = self.app.get('/search/recent/')
        self.assertThat(len(res.json['mail_briefs']), Equals(2))

    def test_recent_index_multiple_message_cur(self):
        self.useMessage('helloworld_2', 'INBOX', 'cur')
        self.indexer.reindex()
        self.fake_getmtime_val += 1
        msg = self.useMessage('helloworld', 'INBOX', 'cur')
        search_api.index_mail(Mail.from_path(msg.dest))
        search_api.refresh()
        res = self.app.get('/search/recent/')
        self.assertThat(len(res.json['mail_briefs']), Equals(2))
        self.assertThat(res.json['mail_briefs'][0]['modified_on'] - 1,
                        Equals(res.json['mail_briefs'][1]['modified_on']))

    def test_recent_index_multiple_message_cur_inverted(self):
        self.useMessage('helloworld', 'INBOX', 'cur')
        self.indexer.reindex()
        self.fake_getmtime_val += 1
        msg = self.useMessage('helloworld_2', 'INBOX', 'cur')
        search_api.index_mail(Mail.from_path(msg.dest))
        search_api.refresh()
        res = self.app.get('/search/recent/')
        self.assertThat(len(res.json['mail_briefs']), Equals(2))
        self.assertThat(res.json['mail_briefs'][0]['modified_on'] - 1,
                        Equals(res.json['mail_briefs'][1]['modified_on']))
