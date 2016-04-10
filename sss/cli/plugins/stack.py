# TODO:

"""Stack Plugin for Simple Setup Server"""

from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from sss.core.variables import SSSVariables
from sss.core.aptget import SSSAptGet
from sss.core.download import SSSDownload
from sss.core.shellexec import SSSShellExec, CommandExecutionError
from sss.core.fileutils import SSSFileUtils
from sss.core.apt_repo import SSSRepo
from sss.core.extract import SSSExtract
from sss.core.mysql import SSSMysql
from sss.core.addswap import SSSSwap
from sss.core.git import SSSGit
from sss.core.checkfqdn import check_fqdn
from sss.core.services import SSSService
from sss.core.variables import SSSVariables
from sss.core.logging import Log
from sss.cli.plugins.stack_migrate import SSSStackMigrateController
from sss.cli.plugins.stack_services import SSSStackStatusController
from sss.cli.plugins.stack_upgrade import SSSStackUpgradeController
import random
import string
import configparser
import time
import shutil
import os
import pwd
import grp
import codecs
import platform

def sss_stack_hook(app):
    #do something with ``app`` object here
    pass

class SSSStackController(CementBaseController):
    class Meta:
        label = 'stack'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'Stack Command'
        usage = "sss stack (command) [options]"
        arguments = [
            (['--all'],
                dict(help='Install all stack', action='store_true')),
            (['--web'],
                dict(help='Install web stack', action='store_true')),
            (['--apache2'],
                dict(help='Install Apache2 stack', action='store_true')),
            (['--php'],
                dict(help='Install PHP7 stack', action='store_true')),
            (['--mysql'],
                dict(help='Install MySQL stack', action='store_true')),
            (['--phpmyadmin'],
                dict(help='Install PHPMyAdmin stack', action='store_true')),
            ]

    @expose(hide=True)
    def default(self):
        """default action of SSS stack command"""
        self.app.args.print_help()

    @expose(hide=True)
    def pre_pref(self,apt_packages):
        """Pre settings to do before installation packages"""

        if set(SSSVariables.sss_mysql).issubset(set(apt_packages)):
            Log.info(self,"Adding repository for MySQL, please wait... ")
            mysql_pref = ("Package: *\nPin: origin sfo1.mirrors.digitalocean.com"
                          "\nPin-Priority: 1000\n")
            with open('/etc/apt/preferences.d/'
                      'MariaDB.pref', 'w') as mysql_pref_file:
                mysql_pref_file.write(mysql_pref)

            SSSRepo.add(self, repo_url=SSSVariables.sss_mysql_repo)
            Log.debug(self, 'Adding key for {0}'
                        .format(SSSVariables.sss_mysql_repo))
            SSSRepo.add_key(self, '0xcbcb082a1bb943db',
                               keyserver="keyserver.ubuntu.com")
            chars = ''.join(random.sample(string.ascii_letters, 8))
            Log.debug(self, "Pre-seeding MySQL")
            Log.debug(self, "echo \"mariadb-server-10.1 "
                      "mysql-server/root_password "
                      "password \" | "
                      "debconf-set-selections")

            try:
                SSSShellExec.cmd_exec(self, "echo \"mariadb-server-10.1 "
                                     "mysql-server/root_password "
                                     "password {chars}\" | "
                                     "debconf-set-selections"
                                     .format(chars=chars),
                                     log=False)
            except CommandExecutionError as e:
                Log.error("Failed to initialize MySQL package")

            Log.debug(self, "echo \"mariadb-server-10.1 "
                      "mysql-server/root_password_again "
                      "password \" | "
                      "debconf-set-selections")

            try:
                SSSShellExec.cmd_exec(self, "echo \"mariadb-server-10.1 "
                                     "mysql-server/root_password_again "
                                     "password {chars}\" | "
                                     "debconf-set-selections"
                                     .format(chars=chars),
                                     log=False)
            except CommandExecutionError as e:
                Log.error("Failed to initialize MySQL package")

            mysql_config = """
            [client]
            user = root
            password = {chars}
            """.format(chars=chars)
            config = configparser.ConfigParser()
            config.read_string(mysql_config)
            Log.debug(self, 'Writting configuration into MySQL file')
            conf_path = "/etc/mysql/conf.d/my.cnf"
            os.makedirs(os.path.dirname(conf_path), exist_ok=True)
            with open(conf_path, encoding='utf-8',
                      mode='w') as configfile:
                config.write(configfile)
            Log.debug(self, 'Setting my.cnf permission')
            SSSFileUtils.chmod(self, "/etc/mysql/conf.d/my.cnf", 0o600)

        if set(SSSVariables.sss_apache).issubset(set(apt_packages)):
            Log.info(self, "Adding repository for Apache, please wait...")
            SSSRepo.add(self, ppa=SSSVariables.sss_apache_repo)

        if set(SSSVariables.sss_php).issubset(set(apt_packages)):
            Log.info(self, "Adding repository for PHP, please wait...")
            Log.debug(self, 'Adding ppa for PHP')
            SSSRepo.add(self, ppa=SSSVariables.sss_php_repo)

    @expose(hide=True)
    def post_pref(self, apt_packages, packages):
        """Post activity after installation of packages"""
        if len(apt_packages):
            if set(SSSVariables.sss_apache).issubset(set(apt_packages)):
                if not (os.path.isfile('/etc/apache2/conf-available/acl.conf')):
                    data = dict(webroot=SSSVariables.sss_webroot)
                    Log.debug(self, 'Writting the Apache configuration to '
                              'file /etc/apache2/conf-available/acl.conf')
                    sss_apache = open('/etc/apache2/conf-available/acl.conf',
                                    encoding='utf-8', mode='w')
                    self.app.render((data), 'acl.mustache',
                                    out=sss_apache)
                    sss_apache.close()

                    # 22222 port setting

                    Log.debug(self, 'Writting the Apache configuration to '
                              'file /etc/apache2/sites-available/'
                              '22222')

                    sss_apache = open('/etc/apache2/sites-available/22222.conf',encoding='utf-8', mode='w')
                    self.app.render((data), '22222.mustache',
                                    out=sss_apache)
                    sss_apache.close()

                    passwd = ''.join([random.choice
                                     (string.ascii_letters + string.digits)
                                     for n in range(6)])

                    try:
                        SSSShellExec.cmd_exec(self, "printf \"SSS:"
                                             "$(openssl passwd -crypt "
                                             "{password} 2> /dev/null)\n\""
                                             "> /etc/apache2/htpasswd-sss "
                                             "2>/dev/null"
                                             .format(password=passwd))
                    except CommandExecutionError as e:
                        Log.error(self, "Failed to save HTTP Auth")

                    # Create Symbolic link for 22222
                    SSSFileUtils.create_symlink(self, ['/etc/apache2/'
                                                      'sites-available/'
                                                      '22222.conf',
                                                      '/etc/apache2/'
                                                      'sites-enabled/'
                                                      '22222.conf'])

                    # Create htdocs folder
                    if not os.path.exists('{0}22222/htdocs'
                                          .format(SSSVariables.sss_webroot)):
                        Log.debug(self, "Creating directory "
                                  "{0}22222/htdocs "
                                  .format(SSSVariables.sss_webroot))
                        os.makedirs('{0}22222/htdocs'
                                    .format(SSSVariables.sss_webroot))

                    if not os.path.exists('/etc/apache2/ssl'):
                        Log.debug(self, "Creating directory "
                                  "/etc/apache2/ssl/")
                        os.makedirs('/etc/apache2/ssl')

                    try:
                        SSSShellExec.cmd_exec(self, "openssl genrsa -out "
                                             "/etc/apache2/ssl/22222.key 2048")
                        SSSShellExec.cmd_exec(self, "openssl req -new -batch  "
                                             "-subj /commonName=127.0.0.1/ "
                                             "-key /etc/apache2/ssl/22222.key "
                                             "-out /etc/apache2/ssl/"
                                             "22222.csr")

                        SSSFileUtils.mvfile(self, "/etc/apache2/ssl/22222.key",
                                           "/etc/apache2/ssl/"
                                           "22222.key.org")

                        SSSShellExec.cmd_exec(self, "openssl rsa -in "
                                             "/etc/apache2/ssl/"
                                             "22222.key.org -out "
                                             "/etc/apache2/ssl/22222.key")

                        SSSShellExec.cmd_exec(self, "openssl x509 -req -days "
                                             "3652 -in /etc/apache2/ssl/"
                                             "22222.csr -signkey "
                                             "/etc/apache2/ssl/22222.key -out "
                                             "/etc/apache2/ssl/22222.crt")

                    except CommandExecutionError as e:
                        Log.error(self, "Failed to generate SSL for 22222")

                    # Apache Configation into GIT
                    SSSGit.add(self,
                              ["/etc/apache2"], msg="Adding Apache into Git")
                    SSSService.restart_service(self, 'apache2')

                    self.msg = (self.msg + ["HTTP Auth User Name: SSS"]
                                + ["HTTP Auth Password : {0}".format(passwd)])

            if set(SSSVariables.sss_php).issubset(set(apt_packages)):
                # Create log directories
                if not os.path.exists('/var/log/php/7.0/'):
                    Log.debug(self, 'Creating directory /var/log/php/7.0/')
                    os.makedirs('/var/log/php/7.0/')

                # TOD : xdebug

                # Parse etc/php5/fpm/php.ini
                config = configparser.ConfigParser()
                Log.debug(self, "configuring php file /etc/php/7.0/fpm/php.ini")
                config.read('/etc/php/7.0/fpm/php.ini')
                config['PHP']['expose_php'] = 'Off'
                config['PHP']['post_max_size'] = '100M'
                config['PHP']['upload_max_filesize'] = '100M'
                config['PHP']['max_execution_time'] = '300'
                config['PHP']['date.timezone'] = SSSVariables.sss_timezone
                with open('/etc/php/7.0/fpm/php.ini',
                          encoding='utf-8', mode='w') as configfile:
                    Log.debug(self, "Writting php configuration into "
                              "/etc/php/7.0/fpm/php.ini")
                    config.write(configfile)

                # Prase /etc/php/7.0/fpm/php-fpm.conf
                config = configparser.ConfigParser()
                Log.debug(self, "configuring php file"
                          "/etc/php/7.0/fpm/php-fpm.conf")
                config.read_file(codecs.open("/etc/php/7.0/fpm/php-fpm.conf",
                                             "r", "utf8"))
                config['global']['error_log'] = '/var/log/php/7.0/fpm.log'
                config.remove_option('global', 'include')
                config['global']['log_level'] = 'notice'
                config['global']['include'] = '/etc/php/7.0/fpm/pool.d/*.conf'
                with codecs.open('/etc/php/7.0/fpm/php-fpm.conf',
                                 encoding='utf-8', mode='w') as configfile:
                    Log.debug(self, "writting php7 configuration into "
                              "/etc/php/7.0/fpm/php-fpm.conf")
                    config.write(configfile)

                # Parse /etc/php/7.0/fpm/pool.d/www.conf
                config = configparser.ConfigParser()
                config.read_file(codecs.open('/etc/php/7.0/fpm/pool.d/www.conf',
                                             "r", "utf8"))
                config['www']['ping.path'] = '/ping'
                config['www']['pm.status_path'] = '/status'
                config['www']['pm.max_requests'] = '500'
                config['www']['pm.max_children'] = '100'
                config['www']['pm.start_servers'] = '20'
                config['www']['pm.min_spare_servers'] = '10'
                config['www']['pm.max_spare_servers'] = '30'
                config['www']['request_terminate_timeout'] = '300'
                config['www']['pm'] = 'ondemand'
                config['www']['listen'] = '127.0.0.1:9000'
                with codecs.open('/etc/php/7.0/fpm/pool.d/www.conf',
                                 encoding='utf-8', mode='w') as configfile:
                    Log.debug(self, "writting PHP5 configuration into "
                              "/etc/php/7.0/fpm/pool.d/www.conf")
                    config.write(configfile)

                #TODO : Debug Config
                #TODO : Disable xdebug

                # PHP and Debug pull configuration
                if not os.path.exists('{0}22222/htdocs/fpm/status/'
                                      .format(SSSVariables.sss_webroot)):
                    Log.debug(self, 'Creating directory '
                              '{0}22222/htdocs/fpm/status/ '
                              .format(SSSVariables.sss_webroot))
                    os.makedirs('{0}22222/htdocs/fpm/status/'
                                .format(SSSVariables.sss_webroot))
                open('{0}22222/htdocs/fpm/status/debug'
                     .format(SSSVariables.sss_webroot),
                     encoding='utf-8', mode='a').close()
                open('{0}22222/htdocs/fpm/status/php'
                     .format(SSSVariables.sss_webroot),
                     encoding='utf-8', mode='a').close()

                # Write info.php
                if not os.path.exists('{0}22222/htdocs/php/'
                                      .format(SSSVariables.sss_webroot)):
                    Log.debug(self, 'Creating directory '
                              '{0}22222/htdocs/php/ '
                              .format(SSSVariables.sss_webroot))
                    os.makedirs('{0}22222/htdocs/php'
                                .format(SSSVariables.sss_webroot))

                with open("{0}22222/htdocs/php/info.php"
                          .format(SSSVariables.sss_webroot),
                          encoding='utf-8', mode='w') as myfile:
                    myfile.write("<?php\nphpinfo();\n?>")

                SSSFileUtils.chown(self, "{0}22222"
                                  .format(SSSVariables.sss_webroot),
                                  SSSVariables.sss_php_user,
                                  SSSVariables.sss_php_user, recursive=True)

                SSSGit.add(self, ["/etc/php/"], msg="Adding PHP into Git")
                SSSService.restart_service(self, 'php7.0-fpm')

            if set(SSSVariables.sss_mysql).issubset(set(apt_packages)):
                if not os.path.isfile("/etc/mysql/my.cnf"):
                    config = ("[mysqld]\nwait_timeout = 30\n"
                              "interactive_timeout=60\nperformance_schema = 0"
                              "\nquery_cache_type = 1")
                    config_file = open("/etc/mysql/my.cnf",
                                       encoding='utf-8', mode='w')
                    config_file.write(config)
                    config_file.close()
                else:
                    try:
                        SSSShellExec.cmd_exec(self, "sed -i \"/#max_conn"
                                             "ections/a wait_timeout = 30 \\n"
                                             "interactive_timeout = 60 \\n"
                                             "performance_schema = 0\\n"
                                             "query_cache_type = 1 \" "
                                             "/etc/mysql/my.cnf")
                    except CommandExecutionError as e:
                        Log.error(self, "Unable to update MySQL file")

                 # Set MySQL Tuning Primer permission
                SSSFileUtils.chmod(self, "/usr/bin/tuning-primer", 0o775)

                SSSGit.add(self, ["/etc/mysql"], msg="Adding MySQL into Git")
                SSSService.reload_service(self, 'mysql')

        if len(packages):
            if any('/tmp/pma.tar.gz' == x[1]
                    for x in packages):
                SSSExtract.extract(self, '/tmp/pma.tar.gz', '/tmp/')
                Log.debug(self, 'Extracting file /tmp/pma.tar.gz to '
                          'location /tmp/')
                if not os.path.exists('{0}22222/htdocs/db'
                                      .format(SSSVariables.sss_webroot)):
                    Log.debug(self, "Creating new  directory "
                              "{0}22222/htdocs/db"
                              .format(SSSVariables.sss_webroot))
                    os.makedirs('{0}22222/htdocs/db'
                                .format(SSSVariables.sss_webroot))
                shutil.move('/tmp/phpmyadmin-STABLE/',
                            '{0}22222/htdocs/db/pma/'
                            .format(SSSVariables.sss_webroot))
                shutil.copyfile('{0}22222/htdocs/db/pma/config.sample.inc.php'
                                .format(SSSVariables.sss_webroot),
                                '{0}22222/htdocs/db/pma/config.inc.php'
                                .format(SSSVariables.sss_webroot))
                Log.debug(self, 'Setting Blowfish Secret Key FOR COOKIE AUTH to  '
                          '{0}22222/htdocs/db/pma/config.inc.php file '
                          .format(SSSVariables.sss_webroot))
                blowfish_key = ''.join([random.choice
                         (string.ascii_letters + string.digits)
                         for n in range(10)])
                SSSFileUtils.searchreplace(self,
                                          '{0}22222/htdocs/db/pma/config.inc.php'
                                          .format(SSSVariables.sss_webroot),
                                          "$cfg[\'blowfish_secret\'] = \'\';","$cfg[\'blowfish_secret\'] = \'{0}\';"
                                          .format(blowfish_key))
                Log.debug(self, 'Setting HOST Server For Mysql to  '
                          '{0}22222/htdocs/db/pma/config.inc.php file '
                          .format(SSSVariables.sss_webroot))
                SSSFileUtils.searchreplace(self,
                                          '{0}22222/htdocs/db/pma/config.inc.php'
                                          .format(SSSVariables.sss_webroot),
                                          "$cfg[\'Servers\'][$i][\'host\'] = \'localhost\';","$cfg[\'Servers\'][$i][\'host\'] = \'{0}\';"
                                          .format(SSSVariables.sss_mysql_host))
                Log.debug(self, 'Setting Privileges of webroot permission to  '
                          '{0}22222/htdocs/db/pma file '
                          .format(SSSVariables.sss_webroot))
                SSSFileUtils.chown(self, '{0}22222'
                                  .format(SSSVariables.sss_webroot),
                                  SSSVariables.sss_php_user,
                                  SSSVariables.sss_php_user,
                recursive=True) 


    @expose(help="Install packages")
    def install(self, packages=[], apt_packages=[], disp_msg=True):
        """Start installation of packages"""
        self.msg = []
        try:
            # Default action for stack installation
            if ((not self.app.pargs.web) and (not self.app.pargs.apache2) and
                (not self.app.pargs.php) and (not self.app.pargs.mysql) and 
                (not self.app.pargs.phpmyadmin)):
                self.app.pargs.web = True
                self.app.pargs.apache2 = True
                self.app.pargs.php = True
                self.app.pargs.mysql = True

            if self.app.pargs.all:
                self.app.pargs.web = True
                self.app.pargs.apache2 = True
                self.app.pargs.php = True
                #self.app.pargs.mysql = True

            if self.app.pargs.web:
                self.app.pargs.apache2 = True
                self.app.pargs.php = True
                #self.app.pargs.mysql = True
                #self.app.pargs.wpcli = True
                #self.app.pargs.postfix = True

            if self.app.pargs.apache2:
                Log.debug(self, "Setting apt_packages variable for Apache2")
                if not SSSAptGet.is_installed(self,'apache2'):
                    apt_packages = apt_packages + SSSVariables.sss_apache

                else :
                    Log.debug(self, "Apache2 already installed")
                    Log.info(self, "Apache2 already installed")

            if self.app.pargs.php:
                Log.debug(self,"Setting apt_packages variable for PHP")
                if not SSSAptGet.is_installed(self,'php7.0-fpm'):
                    apt_packages = apt_packages + SSSVariables.sss_php
                else:
                    Log.debug(self, "PHP already installed")
                    Log.info(self, "PHP already installed")

            if self.app.pargs.mysql:
                Log.debug(self,"Setting apt_packages variable for MySQL")
                if not SSSShellExec.cmd_exec(self,"mysqladmin ping"):
                    apt_packages = apt_packages + SSSVariables.sss_mysql
                    packages = packages + [["https://raw."
                                            "githubusercontent.com"
                                            "/serversetup/tuning-primer/"
                                            "master/tuning-primer.sh",
                                            "/usr/bin/tuning-primer",
                                            "Tuning-Primer"]]
                else:
                    Log.debug(self, "MySQL connection is already alive")
                    Log.info(self, "MySQL connection is already alive")

            if self.app.pargs.phpmyadmin:
                Log.debug(self, "Setting packages varible for phpMyAdmin ")
                packages = packages + [["https://github.com/phpmyadmin/"
                                        "phpmyadmin/archive/STABLE.tar.gz",
                                        "/tmp/pma.tar.gz", "phpMyAdmin"]]


        except Exception as e:
            pass

        if len(apt_packages) or len(packages):
            Log.debug(self,"Calling pre_pref")
            self.pre_pref(apt_packages)
            if len(apt_packages):
                SSSSwap.add(self)
                Log.info(self, "Updating Apt-cache, please wait...")
                SSSAptGet.update(self)
                Log.info(self, "Installing packages, please wait...")
                SSSAptGet.install(self, apt_packages)
                SSSShellExec.cmd_exec(self, "a2enmod proxy_fcgi proxy proxy_http http2 ssl expires headers rewrite")
            if len(packages):
                Log.debug(self, "Downloading following: {0}".format(packages))
                SSSDownload.download(self, packages)
            Log.debug(self, "Calling post_pref")
            self.post_pref(apt_packages, packages)

            if disp_msg:
                if len(self.msg):
                    for msg in self.msg:
                        Log.info(self, Log.ENDC + msg)
                Log.info(self, "Successfully installed packages")
            else:
                return self.msg

    @expose(help="Remove packages")
    def remove(self):
        """Start removal of packages"""
        apt_packages = []
        packages = []

        # Default action for stack remove
        if ((not self.app.pargs.web) and (not self.app.pargs.apache2) and
            (not self.app.pargs.php) and (not self.app.pargs.mysql) and 
            (not self.app.pargs.phpmyadmin)):
                self.app.pargs.web = True
                self.app.pargs.apache2 = True
                self.app.pargs.php = True
                self.app.pargs.mysql = True

        if self.app.pargs.all:
            self.app.pargs.web = True
            self.app.pargs.apache2 = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True

        if self.app.pargs.web:
            self.app.pargs.apache2 = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True
            #self.app.pargs.wpcli = True
            #self.app.pargs.postfix = True

        if self.app.pargs.apache2:
            Log.debug(self,"Removing apt_packages variable of Apache")
            apt_packages = apt_packages + SSSVariables.sss_apache
        if self.app.pargs.php:
            Log.debug(self,"Removing apt_packages variable of PHP")
            apt_packages = apt_packages + SSSVariables.sss_php
        if self.app.pargs.mysql:
            Log.debug(self,"Removing apt_packages variable of PHP")
            apt_packages = apt_packages + SSSVariables.sss_mysql
            packages = packages + ['/usr/bin/tuning-primer']
        if self.app.pargs.phpmyadmin:
            Log.debug(self, "Removing package variable of phpMyAdmin ")
            packages = packages + ['{0}22222/htdocs/db/pma'
            .format(SSSVariables.sss_webroot)]

        if len(packages) or len(apt_packages):
            sss_prompt = input('Are you sure you to want to'
                          ' remove from server.'
                          '\nPackage configuration will remain'
                          ' on server after this operation.\n'
                          'Any answer other than '
                          '"yes" will be stop this'
                          ' operation :  ')

        if sss_prompt == 'YES' or sss_prompt == 'yes':
            if len(packages):
                SSSFileUtils.remove(self, packages)
                SSSAptGet.auto_remove(self)

            if len(apt_packages):
                Log.debug(self, "Removing apt_packages")
                Log.info(self, "Removing packages, please wait...")
                SSSAptGet.remove(self, apt_packages)
                SSSAptGet.auto_remove(self)

            Log.info(self, "Successfully removed packages")

    @expose(help="Purge packages")
    def purge(self):
        """Start purging of packages"""
        apt_packages = []
        packages = []

        # Default action for stack remove
        if ((not self.app.pargs.web) and (not self.app.pargs.apache2) and
            (not self.app.pargs.php) and (not self.app.pargs.mysql) and
            (not self.app.pargs.phpmyadmin)):
                self.app.pargs.web = True
                self.app.pargs.apache2 = True
                self.app.pargs.php = True
                self.app.pargs.mysql = True

        if self.app.pargs.all:
            self.app.pargs.web = True
            self.app.pargs.apache2 = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True

        if self.app.pargs.web:
            self.app.pargs.apache2 = True
            self.app.pargs.php = True
            self.app.pargs.mysql = True
            #self.app.pargs.wpcli = True
            #self.app.pargs.postfix = True

        if self.app.pargs.apache2:
            Log.debug(self, "Purge apt_packages variable of Apache")
            apt_packages = apt_packages + SSSVariables.sss_apache
        if self.app.pargs.php:
            Log.debug(self, "Purge apt_packages variable PHP")
            apt_packages = apt_packages + SSSVariables.sss_php
        if self.app.pargs.mysql:
            Log.debug(self,"Removing apt_packages variable of PHP")
            apt_packages = apt_packages + SSSVariables.sss_mysql
            packages = packages + ['/usr/bin/tuning-primer']
        if self.app.pargs.phpmyadmin:
            packages = packages + ['{0}22222/htdocs/db/pma'.
                                   format(SSSVariables.sss_webroot)]
            Log.debug(self, "Purge package variable phpMyAdmin")

        if len(packages) or len(apt_packages):
            sss_prompt = input('Are you sure you to want to purge '
                              'from server '
                              'along with their configuration'
                              ' packages,\nAny answer other than '
                              '"yes" will be stop this '
                              'operation :')

            if sss_prompt == 'YES' or sss_prompt == 'yes':
                if len(apt_packages):
                    Log.info(self, "Purging packages, please wait...")
                    SSSAptGet.remove(self, apt_packages, purge=True)
                    SSSAptGet.auto_remove(self)

                if len(packages):
                    SSSFileUtils.remove(self, packages)
                    SSSAptGet.auto_remove(self)

                Log.info(self, "Successfully purged packages")

def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(SSSStackController)
    handler.register(SSSStackMigrateController)
    handler.register(SSSStackStatusController)
    handler.register(SSSStackUpgradeController)
    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', sss_stack_hook)
