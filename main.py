# Set up our webserver on a port

# Forward our requests to the given request

# Log the data in the request

# Obtain Response Data

# Log Response Data

# Entry point for starting up a server.
# Uses ProxyBoy class to handle all requests that
# happen to go through our server


from ProxyBoyServer import ProxyBoyServer
from ProxyBoyLogger import ProxyBoyLogger
from ProxyBoy import ProxyBoy
from functools import partial

if __name__ == '__main__':
    import argparse

    # Not saying I'm doing this correctly, for right now. Need to research
    # ArgumentParser a little more.
    parser = argparse.ArgumentParser(
        description="Serves up a proxy server. That's it."
    )

    parser.add_argument('port', action='store',
                    default=1234, type=int,
                    nargs='?',
                    help='Specify alternate port [default: 1234]')

    parser.add_argument('hostname', action='store',
                        default='', type=str,
                        nargs='?',
                        help='Specify alternate hostname [default: 127.0.0.1]')
    parser.add_argument('--ssl', action='store_const',
                        const=True,
                        default=False,
                        help='Flag that you would like to set your proxy up on an SSL connection')
    parser.add_argument('--cert-file', action='store',
                        default="cert.pem", type=str,
                        nargs='?',
                        help='Flag that you would like to set your proxy up on an SSL connection')
    parser.add_argument('--key-file', action='store',
                        default="key.pem", type=str,
                        nargs='?',
                        help='Flag that you would like to set your proxy up on an SSL connection')

    args = parser.parse_args()

    print("Arguments")
    print(args)

    request_handler = partial( ProxyBoy, LoggerClass=ProxyBoyLogger )

    server = ProxyBoyServer(
        request_handler,
        args.hostname,
        args.port,
        args.ssl,
        args.cert_file,
        args.key_file
    )

    server.runServer()
