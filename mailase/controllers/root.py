from pecan.rest import RestController
from wsmeext.pecan import wsexpose

from elasticsearch.client import Elasticsearch
from email.parser import Parser as EmailParser
import os


class Mailbox(object):

    id = str

    def __init__(self, id):
        self.id = id


class Thread(object):

    mail_ids = [str]


class Mail(object):

    id = str
    mailbox_id = str
    subject = str
    thread_id = str

    def __init__(self, id, mailbox_id, subject):
        self.id = id
        self.mailbox_id = mailbox_id
        self.subject = subject


class MailSearchResult(object):

    query = str
    mail_ids = [str]

    def __init__(self, query, mail_ids):
        self.query = query
        self.mail_ids = mail_ids


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
        return 'No valid path found'

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
        search_res = es.search("emails", q=query, fields="_id", size=100)
        mail_ids = [x['_id'] for x in search_res['hits']['hits']]
        return MailSearchResult(query, mail_ids)


class MailController(RestController):

    search = MailSearchController()

    @wsexpose(Mail, str, str)
    def get(self, mailbox_id, mail_id):
        return get_mail_by_id(mailbox_id, mail_id)


class RootController(object):

    mailbox = MailboxController()
    mail = MailController()
