from ProxyBoyBase import ProxyBoyBase
from gzip import open as gzipOpen
from urllib.error import URLError, HTTPError
from urllib.request import build_opener
import curses.ascii
from http import HTTPStatus
import os

class ProxyBoy(ProxyBoyBase):

    def do_CONNECT(self):
        """Performs tunneling"""
        client_url = self.get_client_url()
        self.connection.set_tunnel(client_url)
        self.connection.request("GET", client_url)


    def do_PROXY(self):
        """Proxies requests sent to this network."""
        self.log_request()
        client_url = self.get_client_url()

        # print(self.rfile.peek(-1))
        opener = build_opener()

        # https://tools.ietf.org/html/rfc7230#appendix-A.1.2
        # It is not advised to have Connection: keep-alive or Proxy-Connection: keep-alive
        # headers as part of a proxy request.
        filtered_request_headers = [ header for header in self.headers.items() if header not in self._general_header_exclude ]

        opener.addheaders = filtered_request_headers + [
            ("X-Forwarded-Host", self.headers.get('Host'))
        ]

        # Output headers in output buffer and close buffer,
        # as we do not care a single bit about the headers at this point.
        self.end_headers()
        self.wfile.close()

        # Create a new output buffer to put response information on.
        self.wfile = self.connection.makefile('wb', self.wbufsize)

        try:
            response = opener.open(client_url)

            self.headers = response.getheaders()

            # If response is gzipped then we have to unzip it.
            encoding = response.getheader('Content-Encoding')

            if encoding == 'gzip':
                self.headers = [ header for header in self.headers if not header[0] == 'Content-Encoding' ]
                response = gzipOpen(response)

        except HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print(f"Error code: {e.code}\nError message: {e.reason}")
        except URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        except Exception as e:
            print("We have an exception", e.reason)
        else:
            # This empties the HTTPResponse IOBuffer.
            # Need another implementation to be able to seek
            self.headers = [ header for header in self.headers if header[0] not in self._response_header_exclude ]
            self.send_response(HTTPStatus.OK)
            for header in self.headers:
                self.send_header(header[0], header[1])

            if "Content-Length" not in self.headers:
                fs = os.fstat(response.fileno())
                size = fs[6]
                self.send_header("Content-Length", str(size))

            self.end_headers()

            body = response.read()
            response.close()

            # Output the request response to the user.
            self.wfile.write(body)
        return