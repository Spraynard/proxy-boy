# Set up our webserver on a port

# Forward our requests to the given request

# Log the data in the request

# Obtain Response Data

# Log Response Data

from functools import partial
from io import BytesIO
from urllib.error import URLError, HTTPError
from http import HTTPStatus
import gzip
import http.server
import re
import ssl
import socket
import urllib.parse
import urllib.request

WEBSERVER_ACTIVATE_TEXT="""
Hello! I hope you're doing well.

Your proxy server is being served on:
Address: {ip_address}:{port}
Hostname: {hostname}
"""

class ProxyBoyBase(http.server.BaseHTTPRequestHandler):
    def __init__(self, LoggerClass, request, client_address, server):
        self.logger = LoggerClass
        self._headers_buffer = [] # Needed to not error out. Did I accidentally delete the headers buffer?
        super(ProxyBoyBase, self).__init__(request, client_address, server)

    def do_PROXY(self):
        """
        Main function. Called on every request.
        Must be overriden.
        """
        pass

    def get_a_port(self, parsed_url):
        """Returns a port that is either the default, or a port given in a urlparse() string.
        """
        port = parsed_url.port

        # Search through to find a port string
        if not port:
            port = parsed_url.path.split(':')[-1:][0]

        if not port or (port == parsed_url.path):
            port = 80

        return port

    def get_client_url(self, client_host):
        """Builds and sanitizes the client url string so that we can use it
        in subsequent requests.
        """
        ssl = False
        parsed_url  = urllib.parse.urlparse(client_host, 'http')
        port = self.get_a_port(parsed_url)

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
            # Do a proxy. With ProxyBoy.
            if not getattr(self, 'do_PROXY'):
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self.do_PROXY()
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
        client_url = self.get_client_url(self.headers.get('Host'))

        opener = urllib.request.build_opener()
        opener.addheaders = self.headers.items() + [
            ("X-Forwarded-Host", self.headers.get('Host'))
        ]

        # Output headers in output buffer and close buffer,
        # as we do not care a single bit about the headers at this point.
        self.end_headers()
        self.wfile.close()

        # Create a new output buffer to put response information on.
        self.wfile = self.connection.makefile('wb', self.wbufsize)

        try:
            print(client_url)
            response = opener.open(client_url)
            self.headers = response.getheaders()

            # If response is gzipped then we have to unzip it.
            encoding = response.getheader('Content-Encoding')

            if encoding == 'gzip':
                response = gzip.open(response)

        except HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print(f"Error code: {e.code}\nError message: {e.reason}")
        except URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        else:
            # Output the request response to the user.
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
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                print(WEBSERVER_ACTIVATE_TEXT.format(
                    hostname=hostname, ip_address=ip, port=self.port
                ))
                httpd.socket = ssl.wrap_socket(httpd.socket, server_side=True, certfile='proxypem.pem')
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
    server.runServer()
