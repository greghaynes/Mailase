from elasticsearch.client import Elasticsearch
from pecan import abort
from pecan.rest import RestController
from wsmeext.pecan import wsexpose

from email.parser import Parser as EmailParser
import os


class Mailbox(object):

    id = str

    def __init__(self, id):
        self.id = id


class Mail(object):

    id = str
    mailbox_id = str
    from_ = str
    subject = str
    text_payloads = [str]

    def __init__(self, id, mailbox_id, from_ = None, subject = None):
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
        mail_path_temp = "/home/greghaynes/Mail_testing/%s/%s/%s"
        for subdir in ('cur', 'tmp', 'new'):
            mail_path = mail_path_temp % (self.mailbox_id, subdir, self.id)
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

        text_payloads = []
        for part in msg.walk():
            if part.get_content_type() in ['text/plain']:
                text_payloads.append(part.as_string())
        self.text_payloads = text_payloads


class MailSearchResult(object):

    query = str
    mails = [Mail]

    def __init__(self, query, mails):
        self.query = query
        self.mails = mails


class MailboxController(RestController):

    @wsexpose([Mailbox])
    def index(self):
        return [Mailbox(x) for x in ('INBOX', 'SPAM')]


    @wsexpose(Mailbox, str)
    def get(self, name):
        return Mailbox(name)


class MailSearchController(RestController):

    @wsexpose(MailSearchResult, str)
    def get(self, query):
        es = Elasticsearch([{'host': 'localhost'}])
        search_res = es.search("emails", q=query, fields="from,info_flags,subject", size=100)
        hits = search_res['hits']['hits']

        from_ = lambda x: x['fields']['from'][0]
        subject = lambda x: x['fields']['subject'][0]
        info_flags = lambda x: x['fields']['info_flags'][0]
        mails = [Mail("%s:%s" % (x['_id'], info_flags(x)), '.INBOX', from_(x), subject(x)) for x in hits]
        return MailSearchResult(query, mails)


class MailController(RestController):

    search = MailSearchController()

    @wsexpose(Mail, str, str)
    def get(self, mailbox_id, mail_id):
        mail = Mail(mail_id, mailbox_id)
        if not mail.exists():
            abort(404)
        else:
            mail.load_text_payloads()
            return mail


class RootController(object):

    mailbox = MailboxController()
    mail = MailController()
