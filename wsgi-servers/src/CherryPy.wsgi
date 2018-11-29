import cherrypy
from app import application

if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 9808,
                           })
    app = cherrypy.tree.graft(application, '/')
    cherrypy.engine.start()
    cherrypy.engine.block()
