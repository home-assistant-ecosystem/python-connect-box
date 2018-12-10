"""Exceptions for UPC Connect Box API client."""


class ConnectBoxError(Exception):
    """General ZeroTierError exception occurred."""

    pass


class ConnectBoxConnectionError(ConnectBoxError):
    """When a connection error is encountered."""

    pass


class ConnectBoxNoDataAvailable(ConnectBoxError):
    """When no data is available."""

    pass
