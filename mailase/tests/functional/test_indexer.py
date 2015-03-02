from pecan import conf

from mailase.tests.functional import base


class TestIndexer(base.FunctionalTest):
    def setUp(self):
        super(TestIndexer, self).setUp()
        self.useFixture(base.EsIndexFixture(conf.search.index))
        indexer_fixture = base.IndexerFixture()  # noqa
