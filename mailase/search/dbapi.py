from elasticsearch import Elasticsearch
from pecan import conf

es_client = None


def init(server_url):
    global es_client
    es_client = Elasticsearch(server_url)


def server_is_reachable():
    res = es_client.info()
    return res.get('status') == 200


def refresh():
    es_client.indices.refresh(index=conf.search.index)


def index_mail(mail):
    resp = es_client.index(index=conf.search.index,
                           body=mail.flattened,
                           doc_type='mail',
                           id=mail.brief.id)
    if not resp.get('created'):
        raise RuntimeError('Error when indexing mail id "%s"' % mail.brief.id)


def get_recently_modified(offset, limit):
    res = es_client.search(index=conf.search.index,
                           doc_type='mail',
                           from_=offset,
                           size=limit,)['hits']['hits']
    return [x['_source'] for x in res]
