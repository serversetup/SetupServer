from sss.cli.plugins.stack import SSSStackController
from sss.core.fileutils import SSSFileUtils
from sss.core.mysql import *
from sss.core.shellexec import *
from sss.core.variables import SSSVariables
from sss.cli.plugins.sitedb import *
from sss.core.aptget import SSSAptGet
from sss.core.git import SSSGit
from sss.core.logging import Log
from sss.core.services import SSSService
import subprocess
from subprocess import CalledProcessError
import os
import random
import string
import sys
import getpass
import glob
import re
import platform


class SiteError(Exception):
    """Custom Exception Occured when setting up site"""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


def pre_run_checks(self):

    # Check Apache configuration
    Log.info(self, "Running pre-update checks, please wait...")
    try:
        Log.debug(self, "checking Apache configuration ...")
        FNULL = open('/dev/null', 'w')
        ret = subprocess.check_call(["apachectl", "configtest"], stdout=FNULL,
                                    stderr=subprocess.STDOUT)
    except CalledProcessError as e:
        Log.debug(self, "{0}".format(str(e)))
        raise SiteError("Apache configuration check failed.")


def check_domain_exists(self, domain):
    if getSiteInfo(self, domain):
        return True
    else:
        return False


def setupdomain(self, data):

    sss_domain_name = data['site_name']
    sss_site_webroot = data['webroot'] if 'webroot' in data.keys() else ''

    # Check if Apache configuration already exists
    # if os.path.isfile('/etc/apache2/sites-available/{0}'
    #                   .format(sss_domain_name)):
    #     raise SiteError("Apache configuration already exists for site")

    Log.info(self, "Setting up Apache configuration \t", end='')
    # write apache config for file
    try:
        sss_site_apache_conf = open('/etc/apache2/sites-available/{0}.conf'
                                  .format(sss_domain_name), encoding='utf-8',
                                  mode='w')

        self.app.render((data), 'virtualconf.mustache',
                        out=sss_site_apache_conf)
        sss_site_apache_conf.close()
    except IOError as e:
        Log.debug(self, "{0}".format(e))
        raise SiteError("create apache configuration failed for site")
    except Exception as e:
        Log.debug(self, "{0}".format(e))
        raise SiteError("create apache configuration failed for site")
    finally:
        # check apache config and return status over it
        try:
            Log.debug(self, "Checking generated apache conf, please wait...")
            FNULL = open('/dev/null','w')
            ret = subprocess.check_call(["apachectl", "configtest"], stdout=FNULL,
                                    stderr=subprocess.STDOUT)
            Log.info(self, "[" + Log.ENDC + "Done" + Log.OKGREEN + "]")
        except CalledProcessError as e:
            Log.debug(self, "{0}".format(str(e)))
            Log.info(self, "[" + Log.ENDC + Log.FAIL + "Fail"
                     + Log.ENDC + "]")
            raise SiteError("created apache configuration failed for site."
                            " check with `apachectl configtest`")


    # create Symbolic link
    SSSFileUtils.create_symlink(self, ['/etc/apache2/sites-available/{0}.conf'
                                      .format(sss_domain_name),
                                      '/etc/apache2/sites-enabled/{0}.conf'
                                      .format(sss_domain_name)])

    if 'proxy' in data.keys() and data['proxy']:
        return

    # Creating htdocs & logs directory
    Log.info(self,"Setting up webroot \t\t", end='')
    try:
        if not os.path.exists('{0}/htdocs'.format(sss_site_webroot)):
            os.makedirs('{0}/htdocs'.format(sss_site_webroot))
        if not os.path.exists('{0}/logs'.format(sss_site_webroot)):
            os.makedirs('{0}/logs'.format(sss_site_webroot))

        # Create log file if not exists
        if not os.path.isfile('/var/log/apache2/{0}.access.log'
                                          .format(sss_domain_name)):
                    with open('/var/log/apache2/{0}.access.log'
                                          .format(sss_domain_name),
                              encoding='utf-8', mode='a') as logfile:
                        logfile.close()
        if not os.path.isfile('/var/log/apache2/{0}.error.log'
                                          .format(sss_domain_name)):
                    with open('/var/log/apache2/{0}.error.log'
                                          .format(sss_domain_name),
                              encoding='utf-8', mode='a') as logfile:
                        logfile.close()

        SSSFileUtils.create_symlink(self, ['/var/log/apache2/{0}.access.log'
                                          .format(sss_domain_name),
                                          '{0}/logs/access.log'
                                          .format(sss_site_webroot)])
        SSSFileUtils.create_symlink(self, ['/var/log/apache2/{0}.error.log'
                                          .format(sss_domain_name),
                                          '{0}/logs/error.log'
                                          .format(sss_site_webroot)])

    except Exception as e:
        Log.debug(self, "{0}".format(e))
        raise SiteError("setup webroot failed for site")
    finally:
        # TODO Check if directories are setup
        if (os.path.exists('{0}/htdocs'.format(sss_site_webroot)) and
           os.path.exists('{0}/logs'.format(sss_site_webroot))):
            Log.info(self, "[" + Log.ENDC + "Done" + Log.OKGREEN + "]")
        else:
            Log.info(self, "[" + Log.ENDC + "Fail" + Log.OKGREEN + "]")
            raise SiteError("setup webroot failed for site")

def setupdatabase(self, data):
    sss_domain_name = data['site_name']
    sss_random = (''.join(random.sample(string.ascii_uppercase +
                 string.ascii_lowercase + string.digits, 15)))
    sss_replace_dot = sss_domain_name.replace('.', '_')
    prompt_dbname = self.app.config.get('mysql', 'db-name')
    prompt_dbuser = self.app.config.get('mysql', 'db-user')
    sss_mysql_grant_host = self.app.config.get('mysql', 'grant-host')
    sss_db_name = ''
    sss_db_username = ''
    sss_db_password = ''

    if prompt_dbname == 'True' or prompt_dbname == 'true':
        try:
            sss_db_name = input('Enter the MySQL database name [{0}]: '
                               .format(sss_replace_dot))
        except EOFError as e:
            Log.debug(self, "{0}".format(e))
            raise SiteError("Unable to input database name")

    if not sss_db_name:
        sss_db_name = sss_replace_dot

    if prompt_dbuser == 'True' or prompt_dbuser == 'true':
        try:
            sss_db_username = input('Enter the MySQL database user name [{0}]: '
                                   .format(sss_replace_dot))
            sss_db_password = getpass.getpass(prompt='Enter the MySQL database'
                                             ' password [{0}]: '
                                             .format(sss_random))
        except EOFError as e:
            Log.debug(self, "{0}".format(e))
            raise SiteError("Unable to input database credentials")

    if not sss_db_username:
        sss_db_username = sss_replace_dot
    if not sss_db_password:
        sss_db_password = sss_random

    if len(sss_db_username) > 16:
        Log.debug(self, 'Autofix MySQL username (ERROR 1470 (HY000)),'
                  ' please wait')
        sss_db_username = (sss_db_name[0:6] + generate_random())

    # create MySQL database

    Log.info(self, "Setting up database\t\t", end='')
    Log.debug(self, "Creating database {0}".format(sss_db_name))
    try:
        if SSSMysql.check_db_exists(self, sss_db_name):
            Log.debug(self, "Database already exists, Updating DB_NAME .. ")
            sss_db_name = (sss_db_name[0:6] + generate_random())
            sss_db_username = (sss_db_name[0:6] + generate_random())
    except MySQLConnectionError as e:
        raise SiteError("MySQL Connectivity problem occured")

    try:
        SSSMysql.execute(self, "create database `{0}`"
                        .format(sss_db_name))
    except StatementExcecutionError as e:
        Log.info(self, "[" + Log.ENDC + Log.FAIL + "Failed" + Log.OKGREEN + "]")
        raise SiteError("create database execution failed")

    # Create MySQL User
    Log.debug(self, "Creating user {0}".format(sss_db_username))
    Log.debug(self, "create user `{0}`@`{1}` identified by ''"
              .format(sss_db_username, sss_mysql_grant_host))

    try:
        SSSMysql.execute(self,
                        "create user `{0}`@`{1}` identified by '{2}'"
                        .format(sss_db_username, sss_mysql_grant_host,
                                sss_db_password), log=False)
    except StatementExcecutionError as e:
        Log.info(self, "[" + Log.ENDC + Log.FAIL + "Failed" + Log.OKBLUE + "]")
        raise SiteError("creating user failed for database")

    # Grant permission
    Log.debug(self, "Setting up user privileges")

    try:
        SSSMysql.execute(self,
                        "grant all privileges on `{0}`.* to `{1}`@`{2}`"
                        .format(sss_db_name,
                                sss_db_username, sss_mysql_grant_host))
    except StatementExcecutionError as e:
        Log.info(self, "[" + Log.ENDC + Log.FAIL + "Failed" + Log.OKBLUE + "]")
        SiteError("grant privileges to user failed for database ")

    Log.info(self, "[" + Log.ENDC + "Done" + Log.OKBLUE + "]")

    data['sss_db_name'] = sss_db_name
    data['sss_db_user'] = sss_db_username
    data['sss_db_pass'] = sss_db_password
    data['sss_db_host'] = SSSVariables.sss_mysql_host
    data['sss_mysql_grant_host'] = sss_mysql_grant_host
    return(data)

#def setupwordpress(self, data):
#def setupwordpressnetwork(self, data):
#def installwp_plugin(self, plugin_name, data):
#def uninstallwp_plugin(self, plugin_name, data):
#def setupwp_plugin(self, plugin_name, plugin_option, plugin_data, data):

def setwebrootpermissions(self, webroot):
    Log.debug(self, "Setting up permissions")
    try:
        SSSFileUtils.chown(self, webroot, SSSVariables.sss_php_user,
                          SSSVariables.sss_php_user, recursive=True)
    except Exception as e:
        Log.debug(self, str(e))
        raise SiteError("problem occured while setting up webroot permissions")


#def sitebackup(self, data):


def site_package_check(self,stype):
    apt_packages = []
    packages = []
    stack = SSSStackController()
    stack.app = self.app
    if stype in ['html','php', 'mysql']:
        Log.debug(self,"Setting apt_packages variables for Apache")

        # check if server has apache
        if not SSSAptGet.is_installed(self,'apache2'):
            apt_packages = apt_packages + SSSVariables.sss_apache

    if stype in ['php', 'mysql']:
        Log.debug(self,"Setting apt_packages variables for PHP")

        # check if server has php
        if not SSSAptGet.is_installed(self,'php7.0-fpm'):
            apt_packages = apt_packages + SSSVariables.sss_php

    if stype in ['mysql']:
        Log.debug(self, "Setting apt_packages variable for MySQL")
        if not SSSShellExec.cmd_exec(self, "mysqladmin ping"):
            apt_packages = apt_packages + SSSVariables.sss_mysql
            packages = packages + [["https://raw."
                                    "githubusercontent.com"
                                    "/serversetup/tuning-primer/"
                                    "master/tuning-primer.sh",
                                    "/usr/bin/tuning-primer",
                                    "Tuning-Primer"]]

    return(stack.install(apt_packages=apt_packages, packages=packages,
                         disp_msg=False))


#def updatewpuserpassword(self, sss_domain, sss_site_webroot):
#def display_cache_settings(self, data):

def logwatch(self, logfiles):
    import zlib
    import base64
    import time
    from sss.core import logwatch

    def callback(filename, lines):
        for line in lines:
            if line.find(':::') == -1:
                print(line)
            else:
                data = line.split(':::')
                try:
                    print(data[0], data[1],
                          zlib.decompress(base64.decodestring(data[2])))
                except Exception as e:
                    Log.info(time.time(),
                             'caught exception rendering a new log line in %s'
                             % filename)

    l = logwatch.LogWatcher(logfiles, callback)
    l.loop()

def detSitePar(opts):
    """
        Takes dictionary of parsed arguments
        1.returns sitetype and cachetype
        2. raises RuntimeError when wrong combination is used like
            "--wp --wpsubdir" or "--html --wp"
    """
    sitetype, cachetype = '', ''
    typelist = list()
    cachelist = list()
    for key, val in opts.items():
        if val and key in ['html', 'php', 'mysql', 'wp',
                           'wpsubdir', 'wpsubdomain']:
            typelist.append(key)
        elif val and key in ['wpfc', 'wpsc', 'w3tc', 'wpredis']:
            cachelist.append(key)

    if len(typelist) > 1 or len(cachelist) > 1:
        if len(cachelist) > 1:
            raise RuntimeError("Could not determine cache type.Multiple cache parameter entered")
        elif False not in [x in ('php','mysql','html') for x in typelist]:
            sitetype = 'mysql'
            if not cachelist:
                cachetype = 'basic'
            else:
                cachetype = cachelist[0]
        elif False not in [x in ('php','mysql') for x in typelist]:
            sitetype = 'mysql'
            if not cachelist:
                cachetype = 'basic'
            else:
                cachetype = cachelist[0]
        elif False not in [x in ('html','mysql') for x in typelist]:
            sitetype = 'mysql'
            if not cachelist:
                cachetype = 'basic'
            else:
                cachetype = cachelist[0]
        elif False not in [x in ('php','html') for x in typelist]:
            sitetype = 'php'
            if not cachelist:
                cachetype = 'basic'
            else:
                cachetype = cachelist[0]
        elif False not in [x in ('wp','wpsubdir') for x in typelist]:
            sitetype = 'wpsubdir'
            if not cachelist:
                cachetype = 'basic'
            else:
                cachetype = cachelist[0]
        elif False not in [x in ('wp','wpsubdomain') for x in typelist]:
            sitetype = 'wpsubdomain'
            if not cachelist:
                cachetype = 'basic'
            else:
                cachetype = cachelist[0]
        else:
            raise RuntimeError("could not determine site and cache type")

    else:
        if not typelist and not cachelist:
            sitetype = None
            cachetype = None
        elif (not typelist) and cachelist:
            sitetype = 'wp'
            cachetype = cachelist[0]
        elif typelist and (not cachelist):
            sitetype = typelist[0]
            cachetype = 'basic'
        else:
            sitetype = typelist[0]
            cachetype = cachelist[0]
    return (sitetype, cachetype)


def generate_random():
    sss_random10 = (''.join(random.sample(string.ascii_uppercase +
                   string.ascii_lowercase + string.digits, 10)))
    return sss_random10


def deleteDB(self, dbname, dbuser, dbhost, exit=True):
    try:
        # Check if Database exists
        try:
            if SSSMysql.check_db_exists(self, dbname):
                # Drop database if exists
                Log.debug(self, "dropping database `{0}`".format(dbname))
                SSSMysql.execute(self,
                                "drop database `{0}`".format(dbname),
                                errormsg='Unable to drop database {0}'
                                .format(dbname))
        except StatementExcecutionError as e:
            Log.debug(self, "drop database failed")
            Log.info(self, "Database {0} not dropped".format(dbname))

        except MySQLConnectionError as e:
            Log.debug(self, "Mysql Connection problem occured")

        if dbuser != 'root':
            Log.debug(self, "dropping user `{0}`".format(dbuser))
            try:
                SSSMysql.execute(self,
                                "drop user `{0}`@`{1}`"
                                .format(dbuser, dbhost))
            except StatementExcecutionError as e:
                Log.debug(self, "drop database user failed")
                Log.info(self, "Database {0} not dropped".format(dbuser))
            try:
                SSSMysql.execute(self, "flush privileges")
            except StatementExcecutionError as e:
                Log.debug(self, "drop database failed")
                Log.info(self, "Database {0} not dropped".format(dbname))
    except Exception as e:
        Log.error(self, "Error occured while deleting database", exit)


def deleteWebRoot(self, webroot):
    # do some preprocessing before proceeding
    webroot = webroot.strip()
    if (webroot == "/var/www/" or webroot == "/var/www"
       or webroot == "/var/www/.." or webroot == "/var/www/."):
        Log.debug(self, "Tried to remove {0}, but didn't remove it"
                  .format(webroot))
        return False

    if os.path.isdir(webroot):
        Log.debug(self, "Removing {0}".format(webroot))
        SSSFileUtils.rm(self, webroot)
        return True
    else:
        Log.debug(self, "{0} does not exist".format(webroot))
        return False

def removeApacheConf(self, domain):
    if os.path.isfile('/etc/apache2/sites-available/{0}.conf'
                      .format(domain)):
            Log.debug(self, "Removing Apache configuration")
            SSSFileUtils.rm(self, '/etc/apache2/sites-enabled/{0}.conf'
                           .format(domain))
            SSSFileUtils.rm(self, '/etc/apache2/sites-available/{0}.conf'
                           .format(domain))
            SSSService.reload_service(self, 'apache2')
            SSSGit.add(self, ["/etc/apache2"],
                      msg="Deleted {0} "
                      .format(domain))


def doCleanupAction(self, domain='', webroot='', dbname='', dbuser='',
                    dbhost=''):
    """
       Removes the Apache configuration and database for the domain provided.
       doCleanupAction(self, domain='sitename', webroot='',
                       dbname='', dbuser='', dbhost='')
    """
    if domain:
        if os.path.isfile('/etc/apache2/sites-available/{0}.conf'
                          .format(domain)):
            removeApacheConf(self, domain)
    if webroot:
        deleteWebRoot(self, webroot)

    if dbname:
        if not dbuser:
            raise SiteError("dbuser not provided")
            if not dbhost:
                raise SiteError("dbhost not provided")
        deleteDB(self, dbname, dbuser, dbhost)
