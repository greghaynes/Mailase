import os

from email.parser import Parser as EmailParser
from pecan import conf

import mailase.search.dbapi as search_api


def init_model():
    search_api.init(conf.search.server_url)


class MailBrief(object):
    id = str
    sender = str
    receiver = str
    subject = str

    @classmethod
    def from_message(cls, mail_id, msg):
        return MailBrief(mail_id, msg['from'], msg['to'], msg['subject'])

    def __init__(self, id, sender, receiver, subject):
        self.id = id
        self.sender = sender
        self.receiver = receiver
        self.subject = subject


class Mail(object):
    brief = MailBrief
    text_payloads = [str]

    @classmethod
    def from_disk(cls, mailbox_id, mail_id):
        mail_path = Mail.path_for(mailbox_id, mail_id)
        if mail_path is None:
            return None

        with open(mail_path) as email_fp:
            parser = EmailParser()
            msg = parser.parse(email_fp)

        brief = MailBrief.from_message(mail_id, msg)
        text_payloads = [msg.get_payload()]
        return Mail(brief, text_payloads)

    @classmethod
    def path_for(cls, mailbox_id, mail_id):
        valid = False
        maildir_path = os.path.join(conf.mail.maildirs, mailbox_id)
        for subdir in ('cur', 'new'):
            mail_path = os.path.join(maildir_path, subdir, mail_id)
            try:
                os.stat(mail_path)
                valid = True
                break
            except OSError:
                pass

        if not valid:
            return None
        return mail_path

    def __init__(self, brief, text_payloads):
        self.brief = brief
        self.text_payloads = text_payloads


class Mailbox(object):
    id = str
    mail_briefs = [MailBrief]

    def __init__(self, id, mail_briefs=None):
        self.id = id
        self.mail_briefs = mail_briefs or []

    @property
    def path(self):
        return os.path.join(conf.mail.maildirs, self.id)

    def exists(self):
        return os.path.isdir(self.path)


class MailSearchRecentResult(object):
    offset = int
    limit = int
    mail_briefs = [MailBrief]

    def __init__(self, offset, limit, mail_briefs):
        self.offset = offset
        self.limit = limit
        self.mail_briefs = mail_briefs
