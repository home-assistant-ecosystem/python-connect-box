"""Exceptions for UPC Connect Box API client."""


class ConnectBoxError(Exception):
    """General ZeroTierError exception occurred."""


class ConnectBoxConnectionError(ConnectBoxError):
    """When a connection error is encountered."""


class ConnectBoxNoDataAvailable(ConnectBoxError):
    """When no data is available."""


class ConnectBoxLoginError(ConnectBoxError):
    """When login fails."""
