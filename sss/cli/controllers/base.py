"""Simple Setup Server base controller."""

from cement.core.controller import CementBaseController, expose
from sss.core.variables import SSSVariables
VERSION = SSSVariables.sss_version

BANNER = """
Simple Setup Server v%s
Copyright (c) 2016 GECG.
""" % VERSION


class SSSBaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = ("Simple Setup Servr is the commandline tool to manage your"
                       " websites based on Apache with easy to"
                       " use commands")
        arguments = [
            (['-v', '--version'], dict(action='version', version=BANNER)),
            ]

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()
