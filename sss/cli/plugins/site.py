"""Simple Setup Server site controller."""
from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from sss.core.variables import SSSVariables
from sss.core.domainvalidate import ValidateDomain
from sss.core.fileutils import SSSFileUtils
from sss.cli.plugins.site_functions import *
from sss.core.services import SSSService
from sss.cli.plugins.sitedb import *
from sss.core.git import SSSGit
from subprocess import Popen
import sys
import os
import glob
import subprocess


def sss_site_hook(app):
    # do something with the ``app`` object here.
    from sss.core.database import init_db
    import sss.cli.plugins.models
    init_db(app)


class SSSSiteController(CementBaseController):
    class Meta:
        label = 'site'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = ('Performs website specific operations')
        arguments = [
            (['site_name'],
                dict(help='Website name', nargs='?')),
            ]
        usage = "sss site (command) <site_name> [options]"

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()

    @expose(help="Enable this example.com")
    def enable(self):
        if not self.app.pargs.site_name:
            try:
                while not self.app.pargs.site_name:
                    self.app.pargs.site_name = (input('Enter site name : ')
                                                .strip())
            except IOError as e:
                Log.error(self, 'could not input site name')

        self.app.pargs.site_name = self.app.pargs.site_name.strip()
        # validate domain name
        (sss_domain, sss_www_domain) = ValidateDomain(self.app.pargs.site_name)

        # check if site exists
        if not check_domain_exists(self, sss_domain):
            Log.error(self, "site {0} does not exist".format(sss_domain))
        if os.path.isfile('/etc/apache2/sites-available/{0}.conf'
                          .format(sss_domain)):
            Log.info(self, "Enable domain {0:10} \t".format(sss_domain), end='')
            SSSFileUtils.create_symlink(self,
                                       ['/etc/apache2/sites-available/{0}.conf'
                                        .format(sss_domain),
                                        '/etc/apache2/sites-enabled/{0}.conf'
                                        .format(sss_domain)])
            SSSGit.add(self, ["/etc/apache2"],
                      msg="Enabled {0} "
                      .format(sss_domain))
            updateSiteInfo(self, sss_domain, enabled=True)
            Log.info(self, "[" + Log.ENDC + "OK" + Log.OKGREEN + "]")
            if not SSSService.reload_service(self, 'apache2'):
                Log.error(self, "service Apache2 reload failed. "
                          "check issues with `apachectl configtest` command")
        else:
            Log.error(self, "Apache configuration file does not exist"
                      .format(sss_domain))

    @expose(help="Disable site example.com")
    def disable(self):
        if not self.app.pargs.site_name:
            try:
                while not self.app.pargs.site_name:
                    self.app.pargs.site_name = (input('Enter site name : ')
                                                .strip())

            except IOError as e:
                Log.error(self, 'could not input site name')
        self.app.pargs.site_name = self.app.pargs.site_name.strip()
        (sss_domain, sss_www_domain) = ValidateDomain(self.app.pargs.site_name)
        # check if site exists
        if not check_domain_exists(self, sss_domain):
            Log.error(self, "site {0} does not exist".format(sss_domain))

        if os.path.isfile('/etc/apache2/sites-available/{0}.conf'
                          .format(sss_domain)):
            Log.info(self, "Disable domain {0:10} \t"
                     .format(sss_domain), end='')
            if not os.path.isfile('/etc/apache2/sites-enabled/{0}.conf'
                                  .format(sss_domain)):
                Log.info(self, "[" + Log.FAIL + "Failed" + Log.OKGREEN+"]")
                Log.info(self, "Site {0} already disabled".format(sss_domain))
            else:
                SSSFileUtils.remove_symlink(self,
                                           '/etc/apache2/sites-enabled/{0}.conf'
                                           .format(sss_domain))
                SSSGit.add(self, ["/etc/apache2"],
                          msg="Disabled {0} "
                          .format(sss_domain))
                updateSiteInfo(self, sss_domain, enabled=False)
                Log.info(self, "[" + Log.ENDC + "OK" + Log.OKGREEN + "]")
                if not SSSService.reload_service(self, 'apache2'):
                    Log.error(self, "service apache2 reload failed. "
                              "check issues with `apachectl configtest` command")
        else:
            Log.error(self, "Apache configuration file does not exist"
                      .format(sss_domain))

    @expose(help="Get example.com information")
    def info(self):
        if not self.app.pargs.site_name:
            try:
                while not self.app.pargs.site_name:
                    self.app.pargs.site_name = (input('Enter site name : ')
                                                .strip())
            except IOError as e:
                Log.error(self, 'could not input site name')
        self.app.pargs.site_name = self.app.pargs.site_name.strip()
        (sss_domain, sss_www_domain) = ValidateDomain(self.app.pargs.site_name)
        sss_db_name = ''
        sss_db_user = ''
        sss_db_pass = ''
        hhvm = ''

        if not check_domain_exists(self, sss_domain):
            Log.error(self, "site {0} does not exist".format(sss_domain))
        if os.path.isfile('/etc/apache2/sites-available/{0}.conf'
                          .format(sss_domain)):
            siteinfo = getSiteInfo(self, sss_domain)

            sitetype = siteinfo.site_type
            cachetype = siteinfo.cache_type
            sss_site_webroot = siteinfo.site_path
            access_log = (sss_site_webroot + '/logs/access.log')
            error_log = (sss_site_webroot + '/logs/error.log')
            sss_db_name = siteinfo.db_name
            sss_db_user = siteinfo.db_user
            sss_db_pass = siteinfo.db_password
            sss_db_host = siteinfo.db_host
            if sitetype != "html":
                hhvm = ("enabled" if siteinfo.is_hhvm else "disabled")
            if sitetype == "proxy":
                access_log = "/var/log/apache2/{0}.access.log".format(sss_domain)
                error_log = "/var/log/apache2/{0}.error.log".format(sss_domain)
                sss_site_webroot = ''

            pagespeed = ("enabled" if siteinfo.is_pagespeed else "disabled")

            data = dict(domain=sss_domain, webroot=sss_site_webroot,
                        accesslog=access_log, errorlog=error_log,
                        dbname=sss_db_name, dbuser=sss_db_user,
                        dbpass=sss_db_pass, hhvm=hhvm, pagespeed=pagespeed,
                        type=sitetype + " " + cachetype + " ({0})"
                        .format("enabled" if siteinfo.is_enabled else
                                "disabled"))
            self.app.render((data), 'siteinfo.mustache')
        else:
            Log.error(self, "apache configuration file does not exist"
                      .format(sss_domain))

    @expose(help="Monitor example.com logs")
    def log(self):
        self.app.pargs.site_name = self.app.pargs.site_name.strip()
        (sss_domain, sss_www_domain) = ValidateDomain(self.app.pargs.site_name)
        sss_site_webroot = getSiteInfo(self, sss_domain).site_path

        if not check_domain_exists(self, sss_domain):
            Log.error(self, "site {0} does not exist".format(sss_domain))
        logfiles = glob.glob(sss_site_webroot + '/logs/*.log')
        if logfiles:
            logwatch(self, logfiles)

    @expose(help="Display Apache configuration of example.com")
    def show(self):
        if not self.app.pargs.site_name:
            try:
                while not self.app.pargs.site_name:
                    self.app.pargs.site_name = (input('Enter site name : ')
                                                .strip())
            except IOError as e:
                Log.error(self, 'could not input site name')

        self.app.pargs.site_name = self.app.pargs.site_name.strip()
        (sss_domain, sss_www_domain) = ValidateDomain(self.app.pargs.site_name)

        if not check_domain_exists(self, sss_domain):
            Log.error(self, "site {0} does not exist".format(sss_domain))

        if os.path.isfile('/etc/apache2/sites-available/{0}.conf'
                          .format(sss_domain)):
            Log.info(self, "Display apache2 configuration for {0}.conf"
                     .format(sss_domain))
            f = open('/etc/apache2/sites-available/{0}.conf'.format(sss_domain),
                     encoding='utf-8', mode='r')
            text = f.read()
            Log.info(self, Log.ENDC + text)
            f.close()
        else:
            Log.error(self, "apache2 configuration file does not exists"
                      .format(sss_domain))

    @expose(help="Change directory to site webroot")
    def cd(self):
        if not self.app.pargs.site_name:
            try:
                while not self.app.pargs.site_name:
                    self.app.pargs.site_name = (input('Enter site name : ')
                                                .strip())
            except IOError as e:
                Log.error(self, 'Unable to read input, please try again')

        self.app.pargs.site_name = self.app.pargs.site_name.strip()
        (sss_domain, sss_www_domain) = ValidateDomain(self.app.pargs.site_name)

        if not check_domain_exists(self, sss_domain):
            Log.error(self, "site {0} does not exist".format(sss_domain))

        sss_site_webroot = getSiteInfo(self, sss_domain).site_path
        SSSFileUtils.chdir(self, sss_site_webroot)

        try:
            subprocess.call(['bash'])
        except OSError as e:
            Log.debug(self, "{0}{1}".format(e.errno, e.strerror))
            Log.error(self, "unable to change directory")

class SSSSiteEditController(CementBaseController):
    class Meta:
        label = 'edit'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = ('Edit Apache configuration of site')
        arguments = [
            (['site_name'],
                dict(help='domain name for the site',
                     nargs='?')),
            ]

    @expose(hide=True)
    def default(self):
        if not self.app.pargs.site_name:
            try:
                while not self.app.pargs.site_name:
                    self.app.pargs.site_name = (input('Enter site name : ')
                                                .strip())
            except IOError as e:
                Log.error(self, 'Unable to read input, Please try again')

        self.app.pargs.site_name = self.app.pargs.site_name.strip()
        (sss_domain, sss_www_domain) = ValidateDomain(self.app.pargs.site_name)

        if not check_domain_exists(self, sss_domain):
            Log.error(self, "site {0} does not exist".format(sss_domain))

        sss_site_webroot = SSSVariables.sss_webroot + sss_domain

        if os.path.isfile('/etc/apache2/sites-available/{0}.conf'
                              .format(sss_domain)):
                try:
                    SSSShellExec.invoke_editor(self, '/etc/apache2/sites-availa'
                                              'ble/{0}.conf'.format(sss_domain))
                except CommandExecutionError as e:
                    Log.error(self, "Failed invoke editor")
                if (SSSGit.checkfilestatus(self, "/etc/apache2",
                   '/etc/apache2/sites-available/{0}.conf'.format(sss_domain))):
                    SSSGit.add(self, ["/etc/apache2"], msg="Edit website: {0}"
                              .format(sss_domain))
                    # Reload Apache
                    if not SSSService.reload_service(self, 'apache2'):
                        Log.error(self, "service apache2 reload failed. "
                                  "check issues with `service apache2 reload` command")
        else:
            Log.error(self, "Apache configuration file does not exists"
                          .format(sss_domain))

class SSSSiteCreateController(CementBaseController):
    class Meta:
        label = 'create'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = ('this commands set up configuration and installs '
                       'required files as options are provided')

        arguments = [
            (['site_name'],
                dict(help='domain name for the site to be created.',
                     nargs='?')),
            (['--html'],
                dict(help="create html site", action='store_true')),
            (['--php'],
                dict(help="create php site", action='store_true')),
            (['--mysql'],
                dict(help="create mysql site", action='store_true')),
            (['--proxy'],
                dict(help="create proxy for site", nargs='+')),
            ]

    @expose(hide=True)
    def default(self):
        # self.app.render((data), 'default.mustache')
        # Check domain name validation
        data = dict()
        host,port = None, None
        try:
            stype, cache = detSitePar(vars(self.app.pargs))
        except RuntimeError as e:
            Log.debug(self, str(e))
            Log.error(self, "Please provide valid options to creating site")

        if stype is None and self.app.pargs.proxy:
            stype, cache = 'proxy', ''
            proxyinfo = self.app.pargs.proxy[0].strip()
            if not proxyinfo:
                Log.error(self, "Please provide proxy server host information")
            proxyinfo = proxyinfo.split(':')
            host = proxyinfo[0].strip()
            port = '80' if len(proxyinfo) < 2 else proxyinfo[1].strip()
        elif stype is None and not self.app.pargs.proxy:
            stype, cache = 'html', 'basic'
        elif stype and self.app.pargs.proxy:
            Log.error(self, "proxy should not be used with other site types")
        if (self.app.pargs.proxy and (self.app.pargs.pagespeed
           or self.app.pargs.hhvm)):
            Log.error(self, "Proxy site can not run on pagespeed or hhvm")

        if not self.app.pargs.site_name:
            try:
                while not self.app.pargs.site_name:
                    # preprocessing before finalize site name
                    self.app.pargs.site_name = (input('Enter site name : ')
                                                .strip())
            except IOError as e:
                Log.debug(self, str(e))
                Log.error(self, "Unable to input site name, Please try again!")

        self.app.pargs.site_name = self.app.pargs.site_name.strip()
        (sss_domain, sss_www_domain) = ValidateDomain(self.app.pargs.site_name)

        if not sss_domain.strip():
            Log.error("Invalid domain name, "
                      "Provide valid domain name")

        sss_site_webroot = SSSVariables.sss_webroot + sss_domain

        if check_domain_exists(self, sss_domain):
            Log.error(self, "site {0} already exists".format(sss_domain))
        elif os.path.isfile('/etc/apache2/sites-available/{0}.conf'
                            .format(sss_domain)):
            Log.error(self, "Apache configuration /etc/apache2/sites-available/"
                      "{0} already exists".format(sss_domain))

        if stype in ['html', 'php']:
            data = dict(site_name=sss_domain, www_domain=sss_www_domain,
                        static=True,  basic=False,webroot=sss_site_webroot)

            if stype == 'php':
                data['static'] = False
                data['basic'] = True

        elif stype in ['mysql', 'wp']:
            data = dict(site_name=sss_domain, www_domain=sss_www_domain,
                        static=False,  basic=True, wp=False, w3tc=False,
                        wpfc=False, wpsc=False, wpredis=False, multisite=False,
                        wpsubdir=False, webroot=sss_site_webroot,
                        sss_db_name='', sss_db_user='', sss_db_pass='',
                        sss_db_host='')

        else:
            pass

         # Check rerequired packages are installed or not
        sss_auth = site_package_check(self, stype)

        try:
            pre_run_checks(self)
        except SiteError as e:
            Log.debug(self, str(e))
            Log.error(self, "Apache configuration check failed.")

        try:
            try:
                # setup Apache configuration, and webroot
                setupdomain(self, data)
            except SiteError as e:
                # call cleanup actions on failure
                Log.info(self, Log.FAIL + "Oops Something went wrong !!")
                Log.info(self, Log.FAIL + "Calling cleanup actions ...")
                doCleanupAction(self, domain=sss_domain,
                                webroot=data['webroot'])
                Log.debug(self, str(e))
                Log.error(self, "Check logs for reason "
                          "`tail /var/log/sss/sss.log` & Try Again!!!")

            addNewSite(self, sss_domain, stype, cache, sss_site_webroot)

            # Setup Database for MySQL site
            if 'sss_db_name' in data.keys() and not data['wp']:
                try:
                    data=setupdatabase(self,data)
                    # Add database information for site into database
                    updateSiteInfo(self, sss_domain, db_name=data['sss_db_name'],
                               db_user=data['sss_db_user'],
                               db_password=data['sss_db_pass'],
                               db_host=data['sss_db_host'])

                except SiteError as e:
                    # call cleanup actions on failure
                    Log.debug(self, str(e))
                    Log.info(self, Log.FAIL + "Oops Something went wrong !!")
                    Log.info(self, Log.FAIL + "Calling cleanup actions ...")
                    doCleanupAction(self, domain=sss_domain,
                                    webroot=data['webroot'],
                                    dbname=data['sss_db_name'],
                                    dbuser=data['sss_db_user'],
                                    dbhost=data['sss_db_host'])
                    deleteSiteInfo(self, sss_domain)
                    Log.error(self, "Check logs for reason "
                              "`tail /var/log/sss/sss.log` & Try Again!!!")

                try:
                    sssdbconfig = open("{0}/sss-config.php"
                                  .format(sss_site_webroot),
                                  encoding='utf-8', mode='w')
                    sssdbconfig.write("<?php \ndefine('DB_NAME', '{0}');"
                                     "\ndefine('DB_USER', '{1}'); "
                                     "\ndefine('DB_PASSWORD', '{2}');"
                                     "\ndefine('DB_HOST', '{3}');\n?>"
                                     .format(data['sss_db_name'],
                                             data['sss_db_user'],
                                             data['sss_db_pass'],
                                             data['sss_db_host']))

                    sssdbconfig.close()
                    stype = 'mysql'
                except IOError as e:
                    Log.debug(self.str(e))
                    Log.debug(self, "Error occured while generating "
                              "sss-config.php")
                    Log.info(self, Log.FAIL + "Oops Something went wrong !!")
                    Log.info(self, Log.FAIL + "Calling cleanup actions ...")
                    doCleanupAction(self, domain=sss_domain,
                                    webroot=data['webroot'],
                                    dbname=data['sss_db_name'],
                                    dbuser=data['sss_db_user'],
                                    dbhost=data['sss_db_host'])
                    deleteSiteInfo(self, sss_domain)
                    Log.error(self, "Check logs for reason "
                              "`tail /var/log/sss/sss.log` & Try Again!!!")

            if not SSSService.reload_service(self, 'apache2'):
                Log.info(self, Log.FAIL + "Oops Something went wrong !!")
                Log.info(self, Log.FAIL + "Calling cleanup actions ...")
                doCleanupAction(self, domain=sss_domain,
                                webroot=data['webroot'])
                deleteSiteInfo(self, sss_domain)
                Log.info(self, Log.FAIL + "service Apache reload failed."
                         "check issues with `apachectl configtest` command")
                Log.error(self, "Check logs for reason "
                          "`tail /var/log/sss/sss.log` & Try Again!!!")

            SSSGit.add(self, ["/etc/apache2"],
                      msg="{0} created with {1} {2}"
                      .format(sss_www_domain, stype, cache))

            # Setup Permissions for webroot
            try:
                setwebrootpermissions(self, data['webroot'])
                #fix for log permission

                Log.debug(self,"Fixing Log file Permissions")
                if os.path.isfile('/var/log/apache2/{0}.access.log'
                                          .format(sss_domain)):
                    SSSFileUtils.chown(self,'/var/log/apache2/{0}.access.log'
                                          .format(sss_domain),"root","root")
                if os.path.isfile('/var/log/apache2/{0}.error.log'
                                          .format(sss_domain)):
                    SSSFileUtils.chown(self,'/var/log/apache2/{0}.error.log'
                                          .format(sss_domain),"root","root")

            except SiteError as e:
                Log.debug(self, str(e))
                Log.info(self, Log.FAIL + "Oops Something went wrong !!")
                Log.info(self, Log.FAIL + "Calling cleanup actions ...")
                doCleanupAction(self, domain=sss_domain,
                                webroot=data['webroot'])
                deleteSiteInfo(self, sss_domain)
                Log.error(self, "Check logs for reason "
                          "`tail /var/log/sss/sss.log` & Try Again!!!")

            if sss_auth and len(sss_auth):
                for msg in sss_auth:
                    Log.info(self, Log.ENDC + msg, log=False)

            Log.info(self, "Successfully created site"
                     " http://{0}".format(sss_domain))
        except SiteError as e:
            Log.error(self, "Check logs for reason "
                      "`tail /var/log/sss/sss.log` & Try Again!!!")

#class SSSSiteUpdateController(CementBaseController):

class SSSSiteDeleteController(CementBaseController):
    class Meta:
        label = 'delete'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = 'delete an existing website'
        arguments = [
            (['site_name'],
                dict(help='domain name to be deleted', nargs='?')),
            (['--no-prompt'],
                dict(help="doesnt ask permission for delete",
                     action='store_true')),
            (['--all'],
                dict(help="delete all", action='store_true')),
            (['--db'],
                dict(help="delete db only", action='store_true')),
            (['--files'],
                dict(help="delete webroot only", action='store_true')),
            ]

    @expose(help="Delete website configuration and files")
    @expose(hide=True)
    def default(self):
        if not self.app.pargs.site_name:
            try:
                while not self.app.pargs.site_name:
                    self.app.pargs.site_name = (input('Enter site name : ')
                                                .strip())
            except IOError as e:
                Log.error(self, 'could not input site name')

        self.app.pargs.site_name = self.app.pargs.site_name.strip()
        (sss_domain, sss_www_domain) = ValidateDomain(self.app.pargs.site_name)
        sss_db_name = ''
        sss_prompt = ''
        sss_apache_prompt = ''
        mark_db_deleted = False
        mark_webroot_deleted = False
        if not check_domain_exists(self, sss_domain):
            Log.error(self, "site {0} does not exist".format(sss_domain))

        if ((not self.app.pargs.db) and (not self.app.pargs.files) and
           (not self.app.pargs.all)):
            self.app.pargs.all = True

        # Gather information from sss-db for sss_domain
        check_site = getSiteInfo(self, sss_domain)
        sss_site_type = check_site.site_type
        sss_site_webroot = check_site.site_path
        if sss_site_webroot == 'deleted':
            mark_webroot_deleted = True
        if sss_site_type in ['mysql', 'wp', 'wpsubdir', 'wpsubdomain']:
            sss_db_name = check_site.db_name
            sss_db_user = check_site.db_user
            sss_mysql_grant_host = self.app.config.get('mysql', 'grant-host')
            if sss_db_name == 'deleted':
                mark_db_deleted = True
            if self.app.pargs.all:
                self.app.pargs.db = True
                self.app.pargs.files = True
        else:
            if self.app.pargs.all:
                mark_db_deleted = True
                self.app.pargs.files = True

        if self.app.pargs.db:
            if sss_db_name != 'deleted' and sss_db_name != '':
                if not self.app.pargs.no_prompt:
                    sss_db_prompt = input('Are you sure, you want to delete'
                                         ' database [y/N]: ')
                else:
                    sss_db_prompt = 'Y'

                if sss_db_prompt == 'Y' or sss_db_prompt == 'y':
                    Log.info(self, "Deleting Database, {0}, user {1}"
                             .format(sss_db_name, sss_db_user))
                    deleteDB(self, sss_db_name, sss_db_user, sss_mysql_grant_host, False)
                    updateSiteInfo(self, sss_domain,
                                   db_name='deleted',
                                   db_user='deleted',
                                   db_password='deleted')
                    mark_db_deleted = True
                    Log.info(self, "Deleted Database successfully.")
            else:
                mark_db_deleted = True
                Log.info(self, "Does not seems to have database for this site."
                         )

        # Delete webroot
        if self.app.pargs.files:
            if sss_site_webroot != 'deleted':
                if not self.app.pargs.no_prompt:
                    sss_web_prompt = input('Are you sure, you want to delete '
                                          'webroot [y/N]: ')
                else:
                    sss_web_prompt = 'Y'

                if sss_web_prompt == 'Y' or sss_web_prompt == 'y':
                    Log.info(self, "Deleting Webroot, {0}"
                             .format(sss_site_webroot))
                    deleteWebRoot(self, sss_site_webroot)
                    updateSiteInfo(self, sss_domain, webroot='deleted')
                    mark_webroot_deleted = True
                    Log.info(self, "Deleted webroot successfully")
            else:
                mark_webroot_deleted = True
                Log.info(self, "Webroot seems to be already deleted")

        if (mark_webroot_deleted and mark_db_deleted):
                # TODO Delete Apache conf
                removeApacheConf(self, sss_domain)
                deleteSiteInfo(self, sss_domain)
                Log.info(self, "Deleted site {0}".format(sss_domain))
        # else:
        #     Log.error(self, " site {0} does not exists".format(sss_domain)

class SSSSiteListController(CementBaseController):
    class Meta:
        label = 'list'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = 'List websites'
        arguments = [
            (['--enabled'],
                dict(help='List enabled websites', action='store_true')),
            (['--disabled'],
                dict(help="List disabled websites", action='store_true')),
            ]

    @expose(help="Lists websites")
    def default(self):
            sites = getAllsites(self)
            if not sites:
                pass

            if self.app.pargs.enabled:
                for site in sites:
                    if site.is_enabled:
                        Log.info(self, "{0}".format(site.sitename))
            elif self.app.pargs.disabled:
                for site in sites:
                    if not site.is_enabled:
                        Log.info(self, "{0}".format(site.sitename))
            else:
                for site in sites:
                        Log.info(self, "{0}".format(site.sitename))

def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(SSSSiteController)
    handler.register(SSSSiteCreateController)
    handler.register(SSSSiteEditController)
    handler.register(SSSSiteDeleteController)
    handler.register(SSSSiteListController)
    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', sss_site_hook)
