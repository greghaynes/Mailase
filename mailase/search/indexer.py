import os

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import mailase.search.dbapi as search_api

class MaildirSubdirHandler(FileSystemEventHandler):
    def __init__(self, path):
        super(MonitorHandler, self).__init__()
        self.monitor = monitor
        self.path = path

    def on_created(self, event):
        pass


class Indexer(FileSystemEventHandler):
    def __init__(self, maildirs_path):
        self.maildirs_path = maildirs_path
        self.observer = None

    def start(self):
        if self.observer is not None:
            self.stop()
            self.join()
            del self.observer

        self.observer = Observer()
        for elem in os.listdir(self.maildirs_path):
            for subdir in ('cur', 'new'):
                mail_subdir = os.path.join(self.maildirs_path, elem, subdir)
                if os.isdir(mail_subdir):
                    handler = MaildirSubdirHandler(mail_subdir)
                    self.observer.schedule(handler, mail_subdir)

    def stop(self):
        if self.observer is not None:
            self.observer.stop()

    def join(self):
        if self.observer is not None:
            self.observer.join()

    def reindex(self):
        for elem in os.listdir(self.maildirs_path):
            for subdir in ('cur', 'new'):
                mail_subdir = os.path.join(self.maildirs_path, elem, subdir)
                if os.path.isdir(mail_subdir):
                    self.index_subdir(mail_subdir)

    def index_subdir(self, subdir):
        for elem in os.listdir(subdir):
            if os.path.isfile(os.path.join(subdir, elem)):
                mail_path = os.path.join(subdir, elem)
                search_api.index_mail_path(mail_path)
