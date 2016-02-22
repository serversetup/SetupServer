from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from sss.core.shellexec import SSSShellExec
from sss.core.variables import SSSVariables
from sss.core.logging import Log
from sss.core.git import SSSGit
from sss.core.services import SSSService
import string
import random
import sys
import hashlib
import getpass


def sss_secure_hook(app):
    # do something with the ``app`` object here.
    pass

class SSSSecureController(CementBaseController):
    class Meta:
        label = 'secure'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = ('Secure command secure auth')
        arguments = [
            (['--auth'],
                dict(help='secure auth', action='store_true')),
            (['user_input'],
                dict(help='user input', nargs='?', default=None)),
            (['user_pass'],
                dict(help='user pass', nargs='?', default=None))]
        usage = "sss secure [options]"

    @expose(hide=True)
    def default(self):
        if self.app.pargs.auth:
            self.secure_auth()
        else:
            self.app.args.print_help()

    @expose(hide=True)
    def secure_auth(self):
        """This function Secures authentication"""
        passwd = ''.join([random.choice
                         (string.ascii_letters + string.digits)
                         for n in range(6)])
        if not self.app.pargs.user_input:
            username = input("Provide HTTP authentication user "
                             "name [{0}] :".format(SSSVariables.sss_user))
            self.app.pargs.user_input = username
            if username == "":
                self.app.pargs.user_input = SSSVariables.sss_user
        if not self.app.pargs.user_pass:
            password = getpass.getpass("Provide HTTP authentication "
                                       "password [{0}] :".format(passwd))
            self.app.pargs.user_pass = password
            if password == "":
                self.app.pargs.user_pass = passwd
        Log.debug(self, "printf username:"
                  "$(openssl passwd -crypt "
                  "password 2> /dev/null)\n\""
                  "> /etc/apache2/htpasswd-sss 2>/dev/null")
        SSSShellExec.cmd_exec(self, "printf \"{username}:"
                             "$(openssl passwd -crypt "
                             "{password} 2> /dev/null)\n\""
                             "> /etc/apache2/htpasswd-sss 2>/dev/null"
                             .format(username=self.app.pargs.user_input,
                                     password=self.app.pargs.user_pass),
                             log=False)
        SSSGit.add(self, ["/etc/apache2"],
                  msg="Adding changed secure auth into Git")


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(SSSSecureController)
    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', sss_secure_hook)
