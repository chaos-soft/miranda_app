import os
import threading

import cherrypy

from common import print_error


class Server(threading.Thread):

    def __init__(self, config, messages, base_dir):
        super().__init__()
        self.config = config
        self.messages = messages
        self.base_dir = base_dir
        self.names = config['base'].getlist('names')
        self.start()

    def run(self):
        config = {
            '/store': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': os.path.join(self.base_dir, 'store'),
            },
        }
        cherrypy.config.update({'log.screen': False,
                                'log.access_file': '',
                                'log.error_file': '',
                                'server.socket_host': '0.0.0.0',
                                'server.socket_port': 55555,
                                'engine.autoreload.on': False})

        print_error(self.messages, '{} loaded.'.format(type(self).__name__))
        cherrypy.quickstart(self, '/', config)

    @cherrypy.expose
    def index(self, theme='base'):
        with open(os.path.join(self.base_dir, 'templates/{}.html'.format(theme))) as f:
            return f.read(). \
                replace('{{ names }}', ', '.join('"{}"'.format(n) for n in self.names)). \
                replace('{{ app_name }}', self.config['base']['app_name']). \
                replace('{{ tts_api_key }}', self.config['base'].get('tts_api_key', ''))

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def comments(self, offset):
        return self.messages[int(offset):]

    def stop(self):
        cherrypy.engine.exit()
        # TODO: Почему в данной реализации нужен timeout?
        self.join(0)

        print_error(self.messages, '{} stopped.'.format(type(self).__name__))