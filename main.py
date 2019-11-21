# Set up our webserver on a port

# Forward our requests to the given request

# Log the data in the request

# Obtain Response Data

# Log Response Data

from functools import partial
from io import BytesIO
from urllib.error import URLError, HTTPError
import gzip
import http.server
import re
import ssl
import urllib.parse
import urllib.request

class ProxyBoyBase(http.server.BaseHTTPRequestHandler):
    def __init__(self, LoggerClass, request, client_address, server):
        self.logger = LoggerClass
        super(ProxyBoyBase, self).__init__(request, client_address, server)

    def assign_port(self, parsed_url):
        port = parsed_url.port
        
        # Search through to find a port string
        if not port:
            port = parsed_url.path.split(':')[-1:][0]
       
        if not port or (port == parsed_url.path):
            port = 80

        return port

    def get_client_url(self, client_host):
        ssl = False
        parsed_url  = urllib.parse.urlparse(client_host, 'http')
        port = self.assign_port(parsed_url)

        if port == '443':
            ssl = True

        if not parsed_url.netloc:
            sanitized_url = ":".join(parsed_url.path.split(':')[:-1])

            if not sanitized_url:
                sanitized_url = parsed_url.path

            if ssl:
                parsed_url = parsed_url._replace(scheme='https')
            parsed_url = parsed_url._replace(netloc=f"{sanitized_url}:{port}")
            parsed_url = parsed_url._replace(path="")
        return parsed_url.geturl()

    def handle_one_request(self):
        """Handle a single HTTP request.
        You normally don't need to override this method; see the class
        __doc__ string for information on how to handle specific HTTP
        commands such as GET and POST.
        """
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return
            # Do a proxy. With pyroxy.
            mname = 'do_PROXY'
            method = getattr(self, mname)
            method()
            self.wfile.flush() #actually send the response if not already done.
        except socket.timeout as e:
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

class ProxyBoyLogger():
    def __init__(self):
        self.logger = True

class ProxyBoy(ProxyBoyBase):

    def do_PROXY(self):
        """Proxies requests sent to this network."""
        if not hasattr( self, '_headers_buffer'):
            self._headers_buffer = []
        
        client_url = self.get_client_url(self.headers.get('Host'))

        opener = urllib.request.build_opener()
        opener.addheaders = self.headers.items() + [
            ("X-Forwarded-Host", self.headers.get('Host'))
        ]
        self.end_headers()
        
        self.wfile.close()
        self.wfile = self.connection.makefile('wb', self.wbufsize)

        try:
            print(client_url)
            response = opener.open(client_url)
            self.headers = response.getheaders()
            encoding = response.getheader('Content-Encoding')

            if encoding == 'gzip':
                response = gzip.open(response)
        
        except HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print(f"Error code: {e.code}\nError message: {e.reason}");
            return
        except URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
            return
        else:
       #     # All good, set up the headers for our response
       #     headers = response.info().items()
       #     
       #     for header in self.headers:
       #         self.send_header(header[0], header[1])
            self.wfile.write(response.read())
        return
# Entry point for starting up a server.
# Uses ProxyBoy class to handle all requests that
# happen to go through our server

class ProxyBoyServer:
    def __init__(self, port, LoggerClass):
        self.port = port
        self.logger = LoggerClass
    
    def runServer(self):
        pyroxy_request_handler = partial(ProxyBoy, self.logger)

        with http.server.HTTPServer(('', self.port), pyroxy_request_handler) as httpd:
            try:
                print(f'Now serving on http://localhost.com:{self.port}')
               # httpd.socket = ssl.wrap_socket(httpd.socket, server_side=True, certfile='proxypem.pem')
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nNow shutting down. Thank you for using ProxyBoy\n")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('port', action='store',
                        default=1234, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 1234]')

    args = parser.parse_args()
    
    logger = ProxyBoyLogger()
    server = ProxyBoyServer(args.port, logger)
    server.runServer();
