from ProxyBoyBase import ProxyBoyBase
from gzip import open as gzipOpen
from urllib.error import URLError, HTTPError
from urllib.request import build_opener
import curses.ascii
from http import HTTPStatus
from socketserver import _SocketWriter
import os

class ProxyBoy(ProxyBoyBase):

    def do_CONNECT(self):
        """
        Performs tunneling in order to do a 'correct' proxy request
        in which headers are not modified or read.
        """
        return self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        # # client_url = self.get_client_url()
        # self.connection.set_tunnel(client_url)
        # self.connection.request("GET", client_url)


    def do_PROXY(self):
        """Proxies requests sent to this network."""
        self.log_request()

        client_url = self.get_client_url()

        opener = build_opener()

        # https://tools.ietf.org/html/rfc7230#appendix-A.1.2
        # It is not advised to have Connection: keep-alive or Proxy-Connection: keep-alive
        # headers as part of a proxy request.
        filtered_request_headers = [ header for header in self.headers.items() if header not in self._general_header_exclude ]

        opener.addheaders = filtered_request_headers

        # Output headers in output buffer and close buffer,
        # as we do not care a single bit about the headers at this point.

        # Create a new output buffer to put response information on.
        self.wfile = _SocketWriter(self.connection) #self.connection.makefile('wb', self.wbufsize)

        try:
            # Perform a request to the originally given url
            response = opener.open(client_url)
            self.clear_headers_buffer() # Needed to not include original request headers in response
        except HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print(f"Error code: {e.code}\nError message: {e.reason}")
        except URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        except Exception as e:
            print("Exception")
            print(e)
        else:
            response_headers = [ header for header in response.getheaders() if header[0] not in self._response_header_exclude ]

            # Write down initial status response
            self.send_response(response.status)

            for header in response_headers:
                self.send_header(header[0], header[1])

            self.end_headers()

            body = response.read()
            size = len(body)

            # Explicitly set content length of our request if it
            # is not available in the response headers
            if "Content-Length" not in response_headers:
                self.send_header("Content-Length", str(size))

            response.close()

            # Output the request response to the user.
            self.wfile.write(body)
        return