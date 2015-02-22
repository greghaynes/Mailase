import sys
import json

from wsgiref import simple_server

from mailase.api.app import setup_app


def main():
    config = {
        'app': {
            'root': 'mailase.api.controllers.root.RootController',
            'modules': ['mailase.api'],
        },
        'mail': {
            'maildirs': '/home/greghaynes/Mail_testing'
        }
    }
    app = setup_app(config)
    host = '0.0.0.0'
    port = 8080
    wsgi = simple_server.make_server(host, port, app)

    try:
        wsgi.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
