from elasticsearch import Elasticsearch


es_client = None


def init(server_url):
    global es_client
    es_client = Elasticsearch(server_url)


def server_is_reachable():
    res = es_client.info()
    return res.get('status') == 200


def index_mail_path(mail_path):
    pass

def get_mailbox_recently_modified(mailbox_id, offset, limit):
    pass
