import fixtures
import os
import shutil

from fixtures import Fixture, TempDir
from pecan import set_config
from pecan.testing import load_test_app
from testtools import TestCase


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


class FunctionalTest(TestCase):
    test_data_subdir = 'mailase/tests/data'

    def setUp(self):
        super(FunctionalTest, self).setUp()
        self.test_data_dir = ''.join((os.path.abspath(os.getcwd()), '/',
                                      self.test_data_subdir))
        self.maildir = TempDir()
        self.useFixture(self.maildir)
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
