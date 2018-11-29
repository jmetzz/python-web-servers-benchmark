import logging

def application(environment, start_response):
    """
    The main WSGI Application. Doesn't really do anything
    since we're benchmarking the servers, not this code :)
    """
    logging.warning('Serving request')
    start_response(
        '200 OK',  # Status
        [('Content-type', 'text/plain'), ('Content-Length', '2')]  # Headers
    )
    return [b'OK']
