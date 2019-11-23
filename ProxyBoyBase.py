from ProxyBoyLogger import ProxyBoyLogger
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import errno
import socket

class ProxyBoyBase(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server, LoggerClass=ProxyBoyLogger):
        self.logger = LoggerClass( self )
        self._headers_buffer = [] # Needed to not error out. Did I accidentally delete the headers buffer?
        self._general_header_exclude = [
            ('Connection', 'keep-alive'),
            ('Proxy-Connection', 'keep-alive'),
        ]
        self._response_header_exclude = [
            'Server',
            'Date',
            'Transfer-Encoding'
        ]
        super(ProxyBoyBase, self).__init__(request, client_address, server)

    def clear_headers_buffer(self):
        """
        Clears the headers buffer in this request handler in a way that doesn't write out to our wfile
        """
        self._headers_buffer = []
        return

    def do_PROXY(self):
        """
        Performed on requests in which we want to read information
        """
        pass

    def do_CONNECT(self):
        """
        Performed on requests in which we respect tunneling protocol
        """
        pass

    def log_message(self, format, *args):
        self.logger.log_proxy_boy_message( format, *args )
        return

    def log_error(self, format, *args):
        self.logger.log_proxy_boy_message( format, *args, title="ERROR")

    def log_request(self, code='-', size='-', requestline=None):
        """Log an accepted request.

        This is called by send_response().

        """
        if isinstance(code, HTTPStatus):
            code = code.value

        if not requestline:
            requestline = self.requestline

        self.logger.log_proxy_boy_request('"%s" %s %s', requestline, str(code), str(size))
        return

    def log_response(self, headers):
        self.logger.log_proxy_boy_request('''

''',
            )

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

    def get_client_url(self):
        """Builds and sanitizes the client url string so that we can use it
        in subsequent requests.
        """
        client_host=self.requestline.split(" ")[1]
        ssl = False
        parsed_url  = urlparse(client_host, 'http')
        port = self.get_a_port(parsed_url)

        if port == '443':
            ssl = True

        print("PARSED URL")
        print(parsed_url)

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
            if self.command == "CONNECT":
                self.do_CONNECT()
            else:
                self.do_PROXY()
            # Do a proxy. With ProxyBoy.
            self.wfile.flush() #actually send the response if not already done.
        except socket.timeout as e:
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return
        except IOError as e:
            if e.errno == errno.EPIPE:
                self.log_error("Pipe broken: Trying to perform operations on a closed connection")