import elasticsearch
from fixtures import Fixture
from pecan import conf
from testtools.matchers import Equals

import mailase.search.dbapi as search_api
from mailase.search.indexer import Indexer
from mailase.tests.functional import base


class EsIndexFixture(Fixture):
    def __init__(self, index):
        super(EsIndexFixture, self).__init__()
        self.index = index

    def setUp(self):
        super(EsIndexFixture, self).setUp()
        try:
            search_api.es_client.indices.create(index=self.index)
        except elasticsearch.TransportError as e:
            if e.status_code == 400:
                search_api.es_client.indices.delete(index=self.index)
            else:
                raise

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

    def test_recent_index_single_message(self):
        self.useMessage('helloworld', 'INBOX', 'cur')
        self.indexer.reindex()
