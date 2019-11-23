import sys
import templates

class ProxyBoyLogger():
    def __init__(self, request_handler):
        self.request_handler = request_handler
        self.enabled = True

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def log_proxy_boy_request(self, format, *args):


        self.log_proxy_boy_message(format, *args, title="REQUEST")

        return

    def log_proxy_boy_response(self, format, *args):

        message = templates.PROXY_BOY_LOGGER_REQUEST_TEMPLATE.format(
            message_type="REQUEST",
            address_string=self.request_handler.address_string(),
            datetime_string=self.request_handler.log_date_time_string(),
            data=format%args
        )

        print(message)
        self.log_proxy_boy_message(format, *args, title="RESPONSE" )

    def log_proxy_boy_message(self, format, *args, title=None ):
        """Log an arbitrary message.

        This is used by all other logging functions.  Override
        it if you have specific logging wishes.

        The first argument, FORMAT, is a format string for the
        message to be logged.  If the format string contains
        any % escapes requiring parameters, they should be
        specified as subsequent arguments (it's just like
        printf!).

        The client ip and current date/time are prefixed to
        every message.

        """

        # Default message template
        message = templates.PROXY_BOY_LOGGER_REQUEST_TEMPLATE.format(
            message_type=title.upper(),
            address_string=self.request_handler.address_string(),
            datetime_string=self.request_handler.log_date_time_string(),
            data=format%args
        )

        sys.stderr.write(templates.PROXY_BOY_LOGGER_MESSAGE_TEMPLATE.format(message=message))

        return

    def output_header_list( self, headers ):
            [ self.request_handler.log_message("( %s, %s )", header[0], header[1]) for header in headers ]
            return