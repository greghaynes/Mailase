import elasticsearch
import fixtures
import os
import shutil

from fixtures import Fixture, MonkeyPatch, TempDir
from pecan import conf, set_config
from pecan.testing import load_test_app
from testtools import TestCase

import mailase.search.dbapi as search_api
from mailase.search.indexer import Indexer

class Dir(Fixture):
    def __init__(self, path):
        super(Dir, self).__init__()
        self.path = path

    def setUp(self):
        super(Dir, self).setUp()
        os.mkdir(self.path)

    def cleanUp(self):
        super(Dir, self).cleanUp()
        os.rmdir(self.path)


class CopiedFileFixture(fixtures.Fixture):
    def __init__(self, src, dest):
        super(CopiedFileFixture, self).__init__()
        self.src = src
        self.dest = dest

    def setUp(self):
        super(CopiedFileFixture, self).setUp()
        shutil.copy2(self.src, self.dest)

    def cleanUp(self):
        super(CopiedFileFixture, self).cleanUp()
        os.remove(self.dest)

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


class FunctionalTest(TestCase):
    test_data_subdir = 'mailase/tests/data'

    def setUp(self):
        super(FunctionalTest, self).setUp()
        self.test_data_dir = ''.join((os.path.abspath(os.getcwd()), '/',
                                      self.test_data_subdir))
        self.maildir = TempDir()
        self.useFixture(self.maildir)

        self.fake_getmtime_val = 123456.7
        self.useFixture(MonkeyPatch('os.path.getmtime', self.fake_getmtime))

        config = {
            'app': {
                'root': 'mailase.api.controllers.root.RootController',
                'modules': ['mailase.api'],
            },
            'mail': {
                'maildirs': self.maildir.path
            },
            'search': {
                'server_url': ['http://localhost:9200'],
                'index': 'mailase_test'
            }
        }
        self.app = load_test_app(config)
        self.mailboxes = {}
        self.mua_subdirs = {}

    def tearDown(self):
        super(FunctionalTest, self).tearDown()
        set_config({}, overwrite=True)

    def useMailbox(self, name):
        try:
            mailbox = self.mailboxes[name]
        except KeyError:
            mailbox = Dir(os.path.join(self.maildir.path, name))
            self.mailboxes[name] = mailbox
            self.useFixture(mailbox)
        return mailbox

    def useMailboxSubdir(self, mailbox_name, mua_subdir):
        mailbox = self.useMailbox(mailbox_name)
        if mua_subdir not in ('cur', 'new'):
            raise ValueError('mua_subdir is "%s" but needs to be cur, or new'
                             % mua_subdir)

        subdir_path = os.path.join(mailbox.path, mua_subdir)
        try:
            subdir = self.mua_subdirs[subdir_path]
        except KeyError:
            subdir = Dir(subdir_path)
            self.mua_subdirs[subdir_path] = subdir
            self.useFixture(subdir)
        return subdir

    def useMessage(self, message_name, mailbox_name, mua_subdir='cur', info=''):
        subdir = self.useMailboxSubdir(mailbox_name, mua_subdir)

        msg_src_path = os.path.join(self.test_data_dir, message_name)
        msg_id = message_name + ':' + info
        msg_dest_path = os.path.join(subdir.path, msg_id)

        msg = CopiedFileFixture(msg_src_path, msg_dest_path)
        self.useFixture(msg)
        return msg

    def fake_getmtime(self, path):
        return self.fake_getmtime_val
