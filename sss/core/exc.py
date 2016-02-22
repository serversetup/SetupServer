"""Simple Setup Server exception classes."""


class SSSError(Exception):
    """Generic errors."""
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class SSSConfigError(SSSError):
    """Config related errors."""
    pass


class SSSRuntimeError(SSSError):
    """Generic runtime errors."""
    pass


class SSSArgumentError(SSSError):
    """Argument related errors."""
    pass
