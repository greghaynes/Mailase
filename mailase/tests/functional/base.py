import fixtures
import os
import shutil

from fixtures import TempDir
from pecan import set_config
from pecan.testing import load_test_app
from testtools import TestCase


class CopiedFileFixture(fixtures.Fixture):
    def __init__(self, src, dest):
        self.src = src
        self.dest = dest

    def setUp(self):
        self.addCleanup(self.cleanup)
        shutil.copy2(self.src, self.dest)

    def cleanup(self):
        os.remove(self.dest)


class FunctionalTest(TestCase):

    def setUp(self):
        super(FunctionalTest, self).setUp()
        test_data_subdir = 'mailase/tests/data'
        self.test_data_dir = ''.join((os.path.abspath(os.getcwd()), '/',
                                      test_data_subdir))
        self.maildir = TempDir()
        self.useFixture(self.maildir)
        config = {
            'app': {
                'root': 'mailase.api.controllers.root.RootController',
                'modules': ['mailase.api'],
                'maildirs': [self.maildir.path],
            }
        }
        self.app = load_test_app(config)

    def tearDown(self):
        super(FunctionalTest, self).tearDown()
        set_config({}, overwrite=True)

    def useMessage(self, message_name, subdir='cur', info=''):
        msg_src_path = self.test_data_dir / message_name
        msg_id = message_name + ':' + info
        msg_dest_dir = self.maildir.path / subdir

        if not os.path.isdir(msg_dest_dir):
            os.mkdir(msg_dest_dir)

        msg_dest_path = msg_dest_dir / msg_id
        self.addFixture(CopiedFileFixture(msg_src_path, msg_dest_path))
