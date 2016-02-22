"""Simple Setup Server bootstrapping."""

# All built-in application controllers should be imported, and registered
# in this file in the same way as EEBaseController.

from cement.core import handler
from sss.cli.controllers.base import SSSBaseController


def load(app):
    handler.register(SSSBaseController)
