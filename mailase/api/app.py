from pecan import conf, make_app
from mailase.api import model


def setup_app(config):
    model.init_model()
    app_conf = dict(config['app'])
    conf.update({'mail': config['mail']})

    return make_app(
        app_conf.pop('root'),
        logging=getattr(config, 'logging', {}),
        **app_conf
    )
