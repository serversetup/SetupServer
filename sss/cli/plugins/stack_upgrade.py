from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from sss.core.logging import Log
from sss.core.variables import SSSVariables
from sss.core.aptget import SSSAptGet
from sss.core.apt_repo import SSSRepo
from sss.core.services import SSSService
from sss.core.fileutils import SSSFileUtils
from sss.core.shellexec import SSSShellExec
from sss.core.git import SSSGit
from sss.core.download import SSSDownload
import configparser
import os


class SSSStackUpgradeController(CementBaseController):
    class Meta:
        label = 'upgrade'
        stacked_on = 'stack'
        stacked_type = 'nested'
        description = ('Upgrade stack safely')
        arguments = [
            (['--all'],
                dict(help='Upgrade all stack', action='store_true')),
            (['--web'],
                dict(help='Upgrade web stack', action='store_true')),
            (['--mailscanner'],
                dict(help='Upgrade mail scanner stack', action='store_true')),
            (['--apache2'],
                dict(help='Upgrade Apache stack', action='store_true')),
            (['--php'],
                dict(help='Upgrade PHP stack', action='store_true')),
            (['--mysql'],
                dict(help='Upgrade MySQL stack', action='store_true')),
            (['--no-prompt'],
                dict(help="Upgrade Packages without any prompt",
                     action='store_true')),
            ]

    @expose(hide=True)
    def default(self):
        # All package update
        apt_packages = []
        packages = []

        if ((not self.app.pargs.web) and (not self.app.pargs.apache2) and
           (not self.app.pargs.php) and (not self.app.pargs.mysql) and
            (not self.app.pargs.all)):
            self.app.pargs.web = True

        if self.app.pargs.all:
            self.app.pargs.web = True

        if self.app.pargs.web:
            self.app.pargs.apache2 = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True

        if self.app.pargs.apache2:
            if SSSAptGet.is_installed(self, 'apache2'):
                apt_packages = apt_packages + SSSVariables.sss_apache
            else:
                Log.info(self, "Apache is not already installed")

        if self.app.pargs.php:
            if SSSAptGet.is_installed(self, 'php7.0-fpm'):
                apt_packages = apt_packages + SSSVariables.sss_php
            else:
                Log.info(self, "PHP is not installed")

        if self.app.pargs.mysql:
            if SSSAptGet.is_installed(self, 'mariadb-server'):
                apt_packages = apt_packages + SSSVariables.sss_mysql
            else:
                Log.info(self, "MariaDB is not installed")

        if len(packages) or len(apt_packages):

            Log.info(self, "During package update process non Apache"
                     " parts of your site may remain down")
            # Check prompt
            if (not self.app.pargs.no_prompt):
                start_upgrade = input("Do you want to continue:[y/N]")
                if start_upgrade != "Y" and start_upgrade != "y":
                    Log.error(self, "Not starting package update")

            Log.info(self, "Updating packages, please wait...")
            if len(apt_packages):
                # apt-get update
                SSSAptGet.update(self)
                # Update packages
                SSSAptGet.install(self, apt_packages)

                # Post Actions after package updates
                if set(SSSVariables.sss_apache).issubset(set(apt_packages)):
                    SSSService.restart_service(self, 'apache2')
                if set(SSSVariables.sss_php).issubset(set(apt_packages)):
                    SSSService.restart_service(self, 'php7.0-fpm')
                if set(SSSVariables.sss_mysql).issubset(set(apt_packages)):
                    SSSService.restart_service(self, 'mysql')

            if len(packages):
                pass
            Log.info(self, "Successfully updated packages")
