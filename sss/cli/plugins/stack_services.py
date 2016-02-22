from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from sss.core.services import SSSService
from sss.core.logging import Log
from sss.core.variables import SSSVariables
from sss.core.aptget import SSSAptGet

class SSSStackStatusController(CementBaseController):
    class Meta:
        label = 'stack_services'
        stacked_on = 'stack'
        stacked_type = 'embedded'
        description = 'Get status of stack'
        arguments = [
            (['--memcache'],
                dict(help='start/stop/restart memcache', action='store_true')),
            ]

    @expose(help="Start stack services")
    def start(self):
        """Start services"""
        services = []
        if not (self.app.pargs.apache2 or self.app.pargs.php
                or self.app.pargs.mysql or self.app.pargs.memcache):
            self.app.pargs.apache2 = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True

        if self.app.pargs.apache2:
            if SSSAptGet.is_installed(self,"apache2"):
                services = services + ['apache2']
            else:
                Log.info(self,"Apache is not installed")

        if self.app.pargs.php:
            if SSSAptGet.is_installed(self,'php7.0-fpm'):
                services = services + ['php7.0-fpm']
            else:
                Log.info(self,"PHP7-FPM is not installed")

        if self.app.pargs.mysql:
            if ((SSSVariables.sss_mysql_host is "localhost") or
               (SSSVariables.sss_mysql_host is "127.0.0.1")):
                if (SSSAptGet.is_installed(self, 'mysql-server') or
                   SSSAptGet.is_installed(self, 'percona-server-server-5.6') or
                   SSSAptGet.is_installed(self, 'mariadb-server')):
                    services = services + ['mysql']
                else:
                    Log.info(self, "MySQL is not installed")
            else:
                Log.warn(self, "Remote MySQL found, "
                         "Unable to check MySQL service status")

        if self.app.pargs.memcache:
            if SSSAptGet.is_installed(self, 'memcached'):
                services = services + ['memcached']
            else:
                Log.info(self, "Memcache is not installed")

        for service in services:
            Log.debug(self, "Starting service: {0}".format(service))
            SSSService.start_service(self, service)

    @expose(help="Stop stack services")
    def stop(self):
        """Stop services"""
        services = []
        if not (self.app.pargs.apache2 or self.app.pargs.php
                or self.app.pargs.mysql or self.app.pargs.memcache):
            self.app.pargs.apache2 = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True

        if self.app.pargs.apache2:
            if SSSAptGet.is_installed(self,'apache2'):
                services = services + ['apache2']
            else:
                Log.info(self,'Apache is not installed')

        if self.app.pargs.php:
            if SSSAptGet.is_installed(self, 'php7.0-fpm'):
                services = services + ['php7.0-fpm']
            else:
                Log.info(self, "PHP7-FPM is not installed")

        if self.app.pargs.mysql:
            if ((SSSVariables.sss_mysql_host is "localhost") or
               (SSSVariables.sss_mysql_host is "127.0.0.1")):
                if (SSSAptGet.is_installed(self, 'mysql-server') or
                   SSSAptGet.is_installed(self, 'percona-server-server-5.6') or
                   SSSAptGet.is_installed(self, 'mariadb-server')):
                    services = services + ['mysql']
                else:
                    Log.info(self, "MySQL is not installed")
            else:
                Log.warn(self, "Remote MySQL found, "
                         "Unable to check MySQL service status")

        if self.app.pargs.memcache:
            if SSSAptGet.is_installed(self, 'memcached'):
                services = services + ['memcached']
            else:
                Log.info(self, "Memcache is not installed")

        for service in services:
            Log.debug(self, "Stopping service: {0}".format(service))
            SSSService.stop_service(self, service)

    @expose(help="Restart stack services")
    def restart(self):
        """Restart services"""
        services = []
        if not (self.app.pargs.apache2 or self.app.pargs.php
                or self.app.pargs.mysql or self.app.pargs.memcache):
            self.app.pargs.apache2 = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True

        if self.app.pargs.apache2:
            if SSSAptGet.is_installed(self,'apache2'):
                services = services + ['apache2']
            else:
                Log.info(self,"Apache is not installed")

        if self.app.pargs.php:
            if SSSAptGet.is_installed(self, 'php7.0-fpm'):
                services = services + ['php7.0-fpm']
            else:
                Log.info(self, "PHP7-FPM is not installed")

        if self.app.pargs.mysql:
            if ((SSSVariables.sss_mysql_host is "localhost") or
               (SSSVariables.sss_mysql_host is "127.0.0.1")):
                if (SSSAptGet.is_installed(self, 'mysql-server') or
                   SSSAptGet.is_installed(self, 'percona-server-server-5.6') or
                   SSSAptGet.is_installed(self, 'mariadb-server')):
                    services = services + ['mysql']
                else:
                    Log.info(self, "MySQL is not installed")
            else:
                Log.warn(self, "Remote MySQL found, "
                         "Unable to check MySQL service status")

        if self.app.pargs.memcache:
            if SSSAptGet.is_installed(self, 'memcached'):
                services = services + ['memcached']
            else:
                Log.info(self, "Memcache is not installed")

        for service in services:
            Log.debug(self, "Restarting service: {0}".format(service))
            SSSService.restart_service(self, service)

    @expose(help="Get stack status")
    def status(self):
        """Status of services"""
        services = []
        if not (self.app.pargs.apache2 or self.app.pargs.php
                or self.app.pargs.mysql or self.app.pargs.memcache):
            self.app.pargs.apache2 = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True

        if self.app.pargs.apache2:
            if SSSAptGet.is_installed(self,'apache2'):
                services = services + ['apache2']
            else:
                Log.info(self,"Apache is not installed")

        if self.app.pargs.php:
            if SSSAptGet.is_installed(self, 'php7.0-fpm'):
                services = services + ['php7.0-fpm']
            else:
                Log.info(self, "PHP7-FPM is not installed")

        if self.app.pargs.mysql:
            if ((SSSVariables.sss_mysql_host is "localhost") or
               (SSSVariables.sss_mysql_host is "127.0.0.1")):
                if (SSSAptGet.is_installed(self, 'mysql-server') or
                   SSSAptGet.is_installed(self, 'percona-server-server-5.6') or
                   SSSAptGet.is_installed(self, 'mariadb-server')):
                    services = services + ['mysql']
                else:
                    Log.info(self, "MySQL is not installed")
            else:
                Log.warn(self, "Remote MySQL found, "
                         "Unable to check MySQL service status")

        if self.app.pargs.memcache:
            if SSSAptGet.is_installed(self, 'memcached'):
                services = services + ['memcached']
            else:
                Log.info(self, "Memcache is not installed")

        for service in services:
            if SSSService.get_service_status(self, service):
                Log.info(self, "{0:10}:  {1}".format(service, "Running"))

    @expose(help="Reload stack services")
    def reload(self):
        """Reload service"""
        services = []
        if not (self.app.pargs.apache2 or self.app.pargs.php
                or self.app.pargs.mysql or self.app.pargs.memcache):
            self.app.pargs.apache2 = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True

        if self.app.pargs.apache2:
            if SSSAptGet.is_installed(self,'apache2'):
                services = services + ['apache2']
            else:
                Log.info(self,"Apache is not installed")

        if self.app.pargs.php:
            if SSSAptGet.is_installed(self, 'php7.0-fpm'):
                services = services + ['php7.0-fpm']
            else:
                Log.info(self, "PHP7-FPM is not installed")

        if self.app.pargs.mysql:
            if ((SSSVariables.sss_mysql_host is "localhost") or
               (SSSVariables.sss_mysql_host is "127.0.0.1")):
                if (SSSAptGet.is_installed(self, 'mysql-server') or
                   SSSAptGet.is_installed(self, 'percona-server-server-5.6') or
                   SSSAptGet.is_installed(self, 'mariadb-server')):
                    services = services + ['mysql']
                else:
                    Log.info(self, "MySQL is not installed")
            else:
                Log.warn(self, "Remote MySQL found, "
                         "Unable to check MySQL service status")

        if self.app.pargs.memcache:
            if SSSAptGet.is_installed(self, 'memcached'):
                services = services + ['memcached']
            else:
                Log.info(self, "Memcache is not installed")

        for service in services:
            Log.debug(self, "Reloading service: {0}".format(service))
            SSSService.reload_service(self, service)
