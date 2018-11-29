from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, FallbackHandler, RequestHandler
from tornado.wsgi import WSGIContainer

from app import application

# Documentation on:
# https://www.tornadoweb.org/en/stable/wsgi.html#running-wsgi-apps-on-tornado-servers
# Note from the documentation: WSGI is a synchronous interface,
# while Tornado’s concurrency model is based on single-threaded asynchronous execution. 
# This means that running a WSGI app with Tornado’s WSGIContainer is less scalable than
# running the same app in a multi-threaded WSGI server like gunicorn or uwsgi

# Since Tornado supplies its own HTTPServer, running and deploying it
# is a little different from other Python web frameworks.
# Instead of configuring a WSGI container to find your application,
# you write a main() function that starts the server:

def main(port):
    # Wrap a WSGI function in a WSGIContainer and pass it to HTTPServer to run it
    wsgi_app = WSGIContainer(application)
    
    tornado_app = Application([(".*", wsgi_app),])

    server = HTTPServer(tornado_app)    
    server.bind(port)
    server.start(0)  # forks one process per cpu
    IOLoop.current().start()


if __name__ == '__main__':
    main(9808)



