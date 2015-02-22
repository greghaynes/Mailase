import os

from email.parser import Parser as EmailParser
from pecan import conf


def init_model():
    pass


class Mailbox(object):

    id = str

    def __init__(self, id):
        self.id = id

    @property
    def path(self):
        return os.path.join(conf.mail.maildirs, self.id)

    def exists(self):
        return os.path.isdir(self.path)


class Mail(object):

    id = str
    mailbox_id = str
    from_ = str
    subject = str
    text_payloads = [str]

    def __init__(self, id, mailbox_id, from_=None, subject=None):
        self.id = id
        self.mailbox_id = mailbox_id
        msg = self.msg
        self.from_ = from_
        self.subject = subject
        if msg:
            self.from_ = self.from_ or msg['from']
            self.subject = self.subject or msg['subject']

    @property
    def path(self):
        valid = False
        maildir_path = os.path.join(conf.mail.maildirs, self.mailbox_id)
        for subdir in ('cur', 'tmp', 'new'):
            mail_path = os.path.join(maildir_path, subdir, self.id)
            try:
                os.stat(mail_path)
                valid = True
                break
            except OSError:
                pass

        if not valid:
            return None

        return mail_path

    @property
    def msg(self):
        mail_path = self.path
        if mail_path is None:
            return None

        with open(mail_path) as email_fp:
            parser = EmailParser()
            msg = parser.parse(email_fp)
        return msg

    def exists(self):
        return self.msg is not None

    def load_text_payloads(self):
        msg = self.msg
        if msg is None:
            return

        self.text_payloads = [msg.get_payload()]


class MailSearchResult(object):

    query = str
    mails = [Mail]

    def __init__(self, query, mails):
        self.query = query
        self.mails = mails
