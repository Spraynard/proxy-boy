from functools import partial
from http.server import HTTPServer
import socketserver
import socket
import ssl
import templates
import threading

"""
Saturday 11/23/2019

I currently am getting an OSERROR as seen on socketserver.py line 312.
When connecting explicitly to the server, I see that there is SSL available,
but when I try and proxy requests to the server, I get the OSERROR talked about.
I'm unsure as to the specifics of why this is happening, but I'm pretty sure that there
is something going on with the underlying _ssl.c file.

By my guess, I'm going to have to override the underlying get_request()
method of this HTTPServer in order to do some data wrangling before we do something
with the socket.

I know that a real proxy just uses "tunneling" in order to achieve these effects,
and I might just go ahead and try to implement that because this is turning out to
be a trip to hell.
"""
class ProxyBoyHTTPServer(socketserver.ThreadingTCPServer):
    def __init(self, server_address, RequestHandlerClass):
        super(ProxyBoyHTTPServer, self).__init__(server_address, RequestHandlerClass)
        self.allow_reuse_address = True

class ProxyBoyServer:

    def __init__(self, RequestHandler, hostname, port, ssl, cert_file, key_file):
        """
        Parameters
        __________
        port : int
            The port our webserver will run on
        RequestHandler : ProxyBoy (BaseHTTPRequestHandler)
            Server's request handler. Proxies requests.
        ssl : bool
            Flag whether or not ssl is to be supported

        I know these things have to do with SSL
        cert_file : string
            Cert File... haha... I think it's the root cert that we would put on a device in order to
            say that this traffic is okay.
        key_file : string
            Key File... Unsure. I know that a cert file is needed in order to have a key file.

        """
        self.hostname = hostname
        self.port = port
        self.ssl = ssl
        self.cert_file = cert_file
        self.key_file = key_file
        self.RequestHandler = RequestHandler

    def runServer(self):
        """
        Start up the server little man
        """
        with ProxyBoyHTTPServer((self.hostname, self.port), self.RequestHandler) as httpd:
            ip, port = httpd.server_address
            try:
                hostname = socket.gethostname()
                print(templates.WEBSERVER_ACTIVATE_TEXT.format(hostname=hostname, ip_address=ip, port=port))

                if self.ssl:
                    httpd.socket = ssl.wrap_socket(
                        httpd.socket,
                        certfile=self.cert_file,
                        keyfile=self.key_file,
                        server_side=True
                    )

                server_thread = threading.Thread(target=httpd.serve_forever())
                server_thread.daemon = True
                server_thread.start()

                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nNow shutting down. Thank you for using ProxyBoy\n")
                httpd.shutdown()
                exit()