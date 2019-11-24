# Text that shows when we start up our webserver
WEBSERVER_ACTIVATE_TEXT="""
Hello! I hope you're doing well.

Your proxy server is being served on:
Address: {ip_address}:{port}
Hostname: {hostname}
"""

WEBSERVER_DEACTIVATE_TEXT = "\nNow shutting down. Thank you for using ProxyBoy\n"

# Base Debug Output Message Template
PROXY_BOY_LOGGER_MESSAGE_TEMPLATE="""
*****[PROXY-BOY]************************************************************

{message}

****************************************************************************
"""

# Base Debug Output Request Message Template
PROXY_BOY_LOGGER_REQUEST_TEMPLATE="""
{message_type}
Date: {datetime_string}
Address: {address_string}
Data: {data}
"""

# Base Debug Output Response Message Template
PROXY_BOY_LOGGER_RESPONSE_TEMPLATE="""
{message_type}
Date: {datetime_string}

Headers
===================
{headers}
"""