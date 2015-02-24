from elasticsearch import Elasticsearch, TransportError
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
    return resp


def get_recently_modified(offset, limit, retry_count=3):
    q = {'sort': {'brief.modified_on': {'order': 'desc',
                                        'unmapped_type': 'long'}}}
    try:
        res = es_client.search(index=conf.search.index,
                               doc_type='mail',
                               body=q,
                               from_=offset,
                               size=limit,)['hits']['hits']
        res = [x['_source'] for x in res]
    except TransportError:
        if retry_count > 0:
            res = get_recently_modified(offset, limit, retry_count-1)
        else:
            raise
    return res
