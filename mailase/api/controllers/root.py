import os

from pecan import conf
from pecan.rest import RestController
from wsme import wsproperty
from wsmeext.pecan import wsexpose

from mailase.api.model import (Mail,
                               Mailbox,
                               MailSearchRecentResult)
import mailase.search.dbapi as search_api

class NotFound(Exception):
    code = 404
    msg = "Not Found"

    def __init__(self):
        super(NotFound, self).__init__()


class MailboxController(RestController):
    @wsexpose([Mailbox])
    def index(self):
        mailboxes = []
        for entry in os.listdir(conf.mail.maildirs):
            mailbox = Mailbox(entry)
            if mailbox.exists():
                mailboxes.append(mailbox)
        return mailboxes

    @wsexpose(Mailbox, str, int, int)
    def get(self, mailbox_id, offset=None, limit=None):
        mailbox = Mailbox(mailbox_id)
        if not mailbox.exists():
            raise NotFound
        return mailbox


class SearchRecentControler(RestController):
    @wsexpose(MailSearchRecentResult, int, int)
    def index(self, offset=None, limit=None):
        offset = offset or 0
        limit = limit or 100
        return MailSearchRecentResult(offset, limit, [])


class SearchController(RestController):
    recent = SearchRecentControler()

    @wsexpose(bool)
    def index(self):
        reachable = search_api.server_is_reachable()
        return reachable


class MailController(RestController):
    @wsexpose(Mail, str, str)
    def get(self, mailbox_id, mail_id):
        mail = Mail.from_disk(mailbox_id, mail_id)
        if mail is None:
            raise NotFound()
        else:
            return mail


class RootController(object):
    mailboxes = MailboxController()
    mail = MailController()
    search = SearchController()
