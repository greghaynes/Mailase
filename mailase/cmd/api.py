from wsgiref import simple_server

from mailase.api.app import setup_app


def main():
    app = setup_app()
    host = '0.0.0.0'
    port = '8080'
    wsgi = simple_server.make_server(host, port, app)

    try:
        wsgi.serve_forever()
    except KeyboardInterrupt:
        pass
