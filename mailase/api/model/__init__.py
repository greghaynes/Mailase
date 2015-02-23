import json
import os

from email.parser import Parser as EmailParser
from pecan import conf

import mailase.search.dbapi as search_api


def init_model():
    search_api.init(conf.search.server_url)


class MailBrief(object):
    mailbox_id = str
    id = str
    subdir = str
    sender = str
    receiver = str
    subject = str
    modified_on = int

    @classmethod
    def from_message(cls, mailbox_id, mail_id, subdir, msg, modified_on):
        return MailBrief(mailbox_id, mail_id, subdir, msg['from'], msg['to'],
                         msg['subject'], modified_on)

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(json_data)
        return cls.from_obj(data)

    @classmethod
    def from_obj(cls, data):
        return MailBrief(data['mailbox_id'], data['id'], data['subdir'],
                         data['sender'], data['receiver'], data['subject'],
                         data['modified_on'])

    def __init__(self, mailbox_id, id, subdir, sender, receiver, subject,
                 modified_on):
        self.mailbox_id = mailbox_id
        self.id = id
        self.subdir = subdir
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.modified_on = modified_on

    @property
    def json(self):
        return json.dumps({'mailbox_id': self.mailbox_id,
                           'id': self.id,
                           'subdir': self.subdir,
                           'sender': self.sender,
                           'receiver': self.receiver,
                           'subject': self.subject,
                           'modified_on': self.modified_on})


class Mail(object):
    brief = MailBrief
    text_payloads = [str]

    @classmethod
    def from_path(cls, path):
        if not path.startswith(conf.mail.maildirs):
            raise ValueError('Path "%s" is not in the maildirs path' % path)

        tmp_path = path.replace(conf.mail.maildirs, '', 1)
        if tmp_path.startswith('/'):
            tmp_path = tmp_path[1:]
        mailbox_id, subdir, mail_id = tmp_path.split('/')

        with open(path) as email_fp:
            parser = EmailParser()
            msg = parser.parse(email_fp)

        mtime = int(os.path.getmtime(path))
        brief = MailBrief.from_message(mailbox_id, mail_id, subdir, msg, mtime)
        text_payloads = [msg.get_payload()]
        return Mail(brief, text_payloads)

    @classmethod
    def from_id(cls, mailbox_id, mail_id, subdir=None):
        if subdir is None:
            mail_path = cls.path_for(mailbox_id, mail_id)
            if mail_path is None:
                raise ValueError('Could not find message with id "%s" in '\
                                 'mailbox "%s"' % (mail_id, mailbox_id))
        else:
            mail_path = os.path.join(conf.mail.maildirs, mailbox_id, subdir,
                                     mail_id)
            if not os.path.isfile(mail_path):
                raise ValueError('Could not find message at path "%s"'
                                 % mail_path)
        return cls.from_path(mail_path)

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(json_data)
        return Mail(data['brief'], data['text_payloads'])

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

    @property
    def json(self):
        return json.dumps({'brief': self.brief.json,
                           'text_payloads': self.text_payloads})


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
