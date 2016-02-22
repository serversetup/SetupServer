"""SimpleSetupServer core variable module"""
import platform
import socket
import configparser
import os
import sys
import psutil
import datetime

class SSSVariables():
    """Intialization of core variables"""

    # Simple Setup Server version
    sss_version = "1.0.0"


	# Current date and time of System
    sss_date = datetime.datetime.now().strftime('%d%b%Y%H%M%S')

    # Simple Setup Server core variables
    sss_platform_distro = platform.linux_distribution()[0].lower()
    sss_platform_version = platform.linux_distribution()[1]
    sss_platform_codename = os.popen("lsb_release -sc | tr -d \'\\n\'").read()

    # Get timezone of system
    if os.path.isfile('/etc/timezone'):
        with open("/etc/timezone", "r") as tzfile:
            sss_timezone = tzfile.read().replace('\n', '')
            if sss_timezone == "Etc/UTC":
                sss_timezone = "UTC"
    else:
        sss_timezone = "UTC"

    # Get FQDN of system
    sss_fqdn = socket.getfqdn()

    # Simple Setup Server default webroot path
    sss_webroot = '/var/www/'

    # PHP5 user
    sss_php_user = 'www-data'

    # Get git user name and EMail
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~")+'/.gitconfig')
    try:
        sss_user = config['user']['name']
        sss_email = config['user']['email']
    except Exception as e:
        sss_user = input("Enter your name: ")
        sss_email = input("Enter your email: ")
        os.system("git config --global user.name {0}".format(sss_user))
        os.system("git config --global user.email {0}".format(sss_email))

    # Get System RAM and SWAP details
    sss_ram = psutil.virtual_memory().total / (1024 * 1024)
    sss_swap = psutil.swap_memory().total / (1024 * 1024)

    # Apache
    sss_apache = ["apache2"]
    sss_apache_repo = "ppa:ondrej/apache2"

    # MySQL hostname
    sss_mysql_host = ""
    config = configparser.RawConfigParser()
    cnfpath = os.path.expanduser("~")+"/.my.cnf"
    if [cnfpath] == config.read(cnfpath):
        try:
            sss_mysql_host = config.get('client', 'host')
        except configparser.NoOptionError as e:
            sss_mysql_host = "localhost"
    else:
        sss_mysql_host = "localhost"

    # PHP repo and packages
    if sss_platform_distro == 'ubuntu':
        sss_php_repo = "ppa:ondrej/php"
    sss_php = ["php7.0-fpm", "php7.0-curl", "php7.0-gd", "php7.0-imap",
              "php7.0-mcrypt", "php7.0-common", "php7.0-readline",
              "php7.0-mysql", "php7.0-cli", "php-memcached", "php-imagick",
              "memcached", "graphviz", "php-pear"]

    # if sss_platform_distro == 'ubuntu':
    #     sss_php = sss_php + ["php7.0-xdebug"]

    # MySQL repo and packages
    if sss_platform_distro == 'ubuntu':
        sss_mysql_repo = ("deb http://mirror.aarnet.edu.au/pub/MariaDB/repo/"
                         "10.1/ubuntu {codename} main"
                         .format(codename=sss_platform_codename))

    sss_mysql = ["mariadb-server", "percona-toolkit"]


    # Repo path
    sss_repo_file = "ss-repo.list"
    sss_repo_file_path = ("/etc/apt/sources.list.d/" + sss_repo_file)

    # Application dabase file path
    basedir = os.path.abspath(os.path.dirname('/var/lib/sss/'))
    sss_db_uri = 'sqlite:///' + os.path.join(basedir, 'sss.db')

    def __init__(self):
        pass
