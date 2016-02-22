"""SSINFO Plugin for EasyEngine."""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from sss.core.aptget import SSSAptGet
from sss.core.shellexec import SSSShellExec
from sss.core.logging import Log
import os
import configparser


def sss_info_hook(app):
    # do something with the ``app`` object here.
    pass

class SSSInfoController(CementBaseController):
    class Meta:
        label = 'info'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = ('Display configuration information related to Apache,'
                       ' PHP and MySQL')
        arguments = [
            (['--mysql'],
                dict(help='Get MySQL configuration information',
                     action='store_true')),
            (['--php'],
                dict(help='Get PHP configuration information',
                     action='store_true')),
            (['--apache2'],
                dict(help='Get Apache configuration information',
                     action='store_true')),
            ]
        usage = "sss info [options]"

    # @expose(hide=True)
    # def info_nginx(self):
    # TODO : Need to Create Lots of Grep Commands

    @expose(hide=True)
    def info_php(self):
        """Display PHP information"""
        version = os.popen("php -v | head -n1 | cut -d' ' -f2 |"
                           " cut -d'+' -f1 | tr -d '\n'").read
        config = configparser.ConfigParser()
        config.read('/etc/php/7.0/fpm/php.ini')
        expose_php = config['PHP']['expose_php']
        memory_limit = config['PHP']['memory_limit']
        post_max_size = config['PHP']['post_max_size']
        upload_max_filesize = config['PHP']['upload_max_filesize']
        max_execution_time = config['PHP']['max_execution_time']

        config.read('/etc/php/7.0/fpm/pool.d/www.conf')
        www_listen = config['www']['listen']
        www_ping_path = config['www']['ping.path']
        www_pm_status_path = config['www']['pm.status_path']
        www_pm = config['www']['pm']
        www_pm_max_requests = config['www']['pm.max_requests']
        www_pm_max_children = config['www']['pm.max_children']
        www_pm_start_servers = config['www']['pm.start_servers']
        www_pm_min_spare_servers = config['www']['pm.min_spare_servers']
        www_pm_max_spare_servers = config['www']['pm.max_spare_servers']
        www_request_terminate_time = (config['www']
                                            ['request_terminate_timeout'])
        try:
            www_xdebug = (config['www']['php_admin_flag[xdebug.profiler_enable'
                                        '_trigger]'])
        except Exception as e:
            www_xdebug = 'off'

        data = dict(version=version, expose_php=expose_php,
                    memory_limit=memory_limit, post_max_size=post_max_size,
                    upload_max_filesize=upload_max_filesize,
                    max_execution_time=max_execution_time,
                    www_listen=www_listen, www_ping_path=www_ping_path,
                    www_pm_status_path=www_pm_status_path, www_pm=www_pm,
                    www_pm_max_requests=www_pm_max_requests,
                    www_pm_max_children=www_pm_max_children,
                    www_pm_start_servers=www_pm_start_servers,
                    www_pm_min_spare_servers=www_pm_min_spare_servers,
                    www_pm_max_spare_servers=www_pm_max_spare_servers,
                    www_request_terminate_timeout=www_request_terminate_time,
                    www_xdebug_profiler_enable_trigger=www_xdebug)
        self.app.render((data), 'info_php.mustache')

    @expose(hide=True)
    def info_mysql(self):
        """Display MySQL information"""
        version = os.popen("mysql -V | awk '{print($5)}' | cut -d ',' "
                           "-f1 | tr -d '\n'").read()
        host = "localhost"
        port = os.popen("mysql -e \"show variables\" | grep ^port | awk "
                        "'{print($2)}' | tr -d '\n'").read()
        wait_timeout = os.popen("mysql -e \"show variables\" | grep "
                                "^wait_timeout | awk '{print($2)}' | "
                                "tr -d '\n'").read()
        interactive_timeout = os.popen("mysql -e \"show variables\" | grep "
                                       "^interactive_timeout | awk "
                                       "'{print($2)}' | tr -d '\n'").read()
        max_used_connections = os.popen("mysql -e \"show global status\" | "
                                        "grep Max_used_connections | awk "
                                        "'{print($2)}' | tr -d '\n'").read()
        datadir = os.popen("mysql -e \"show variables\" | grep datadir | awk"
                           " '{print($2)}' | tr -d '\n'").read()
        socket = os.popen("mysql -e \"show variables\" | grep \"^socket\" | "
                          "awk '{print($2)}' | tr -d '\n'").read()
        data = dict(version=version, host=host, port=port,
                    wait_timeout=wait_timeout,
                    interactive_timeout=interactive_timeout,
                    max_used_connections=max_used_connections,
                    datadir=datadir, socket=socket)
        self.app.render((data), 'info_mysql.mustache')

    @expose(hide=True)
    def default(self):
        """default function for info"""
        if (not self.app.pargs.apache2 and not self.app.pargs.php
           and not self.app.pargs.mysql):
            self.app.pargs.apache2 = False
            self.app.pargs.php = True
            self.app.pargs.mysql = True

        if self.app.pargs.apache2:
            if SSSAptGet.is_installed(self, 'apache2'):
                self.info_apache2()
            else:
                Log.error(self, "Apache is not installed")

        if self.app.pargs.php:
            if SSSAptGet.is_installed(self, 'php7.0-fpm'):
                self.info_php()
            else:
                Log.error(self, "PHP5 is not installed")

        if self.app.pargs.mysql:
            if SSSShellExec.cmd_exec(self, "mysqladmin ping"):
                self.info_mysql()
            else:
                Log.error(self, "MySQL is not installed")


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(SSSInfoController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', sss_info_hook)
