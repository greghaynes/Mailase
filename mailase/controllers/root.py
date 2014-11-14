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


class MailSummary(object):

    id = str
    mailbox_id = str
    subject = str
    href = str

    def __init__(self, id, mailbox_id, subject):
        self.id = id
        self.mailbox_id = mailbox_id
        self.subject = subject
        self.href = "http://localhost:8080/mail/%s/%s" % (self.mailbox_id, self.id)


class Mail(MailSummary):

    def __init__(self, id, mailbox_id, subject):
        super(Mail, self).__init__(id, mailbox_id, subject)


class MailSearchResult(object):

    query = str
    mails = [MailSummary]

    def __init__(self, query, mails):
        self.query = query
        self.mails = mails


def get_mail_by_id(mailbox_id, mail_id):
    valid = False
    for subdir in ('cur', 'tmp', 'new'):
        mail_path = "/home/greghaynes/Mail_testing/%s/%s/%s" % (mailbox_id,
                                                                   subdir,
                                                                   mail_id)
        try:
            os.stat(mail_path)
            valid = True
            break
        except OSError:
            pass
    
    if not valid:
        return None

    with open(mail_path) as email_fp:
        parser = EmailParser()
        msg = parser.parse(email_fp)
        return Mail(mail_id, mailbox_id, msg['subject'])


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
        search_res = es.search("emails", q=query, fields="subject", size=100)
        hits = search_res['hits']['hits']
        mails = [MailSummary(x['_id'], '.INBOX', x['fields']['subject'][0]) for x in hits]
        return MailSearchResult(query, mails)


class MailController(RestController):

    search = MailSearchController()

    @wsexpose(Mail, str, str)
    def get(self, mailbox_id, mail_id):
        return get_mail_by_id(mailbox_id, mail_id) or abort(404)


class RootController(object):

    mailbox = MailboxController()
    mail = MailController()
