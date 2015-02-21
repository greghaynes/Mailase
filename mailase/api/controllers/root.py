import os

from elasticsearch.client import Elasticsearch
from pecan import abort, conf
from pecan.rest import RestController
from wsmeext.pecan import wsexpose

from mailase.api.model import (Mail,
                               Mailbox,
                               MailSearchResult)

class MailboxController(RestController):

    @wsexpose([Mailbox])
    def index(self):
        maildirs = []
        for maildir in conf.mail.maildirs:
            for entry in os.listdir(maildir):
                if os.path.isdir(os.path.join(maildir, entry)):
                    maildirs.append(entry)
        return [Mailbox(x) for x in maildirs]

    @wsexpose(Mailbox, str)
    def get(self, name):
        return Mailbox(name)


class MailSearchController(RestController):

    @wsexpose(MailSearchResult, str)
    def get(self, query):
        es = Elasticsearch([{'host': 'localhost'}])
        search_res = es.search("emails", q=query,
                               fields="from,info_flags,subject",
                               size=100)
        hits = search_res['hits']['hits']

        from_ = lambda x: x['fields']['from'][0]
        subject = lambda x: x['fields']['subject'][0]
        info_flags = lambda x: x['fields']['info_flags'][0]
        mails = [Mail("%s:%s" % (x['_id'], info_flags(x)),
                      '.INBOX',from_(x),subject(x)) for x in hits]
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
