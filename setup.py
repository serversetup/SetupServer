import sys
import os
import glob
import configparser
import re
from setuptools import setup, find_packages
conf = []
templates = []

long_description = '''Simple Setup Server is the commandline tool to manage your Linux Server'''

for name in glob.glob('config/plugins.d/*.conf'):
    conf.insert(1, name)

for name in glob.glob('sss/cli/templates/*.mustache'):
    templates.insert(1, name)

if not os.path.exists('/var/log/sss/'):
    os.makedirs('/var/log/sss/')

if not os.path.exists('/var/lib/sss/'):
    os.makedirs('/var/lib/sss/')

# Simple Server Setup git function
config = configparser.ConfigParser()
config.read(os.path.expanduser("~")+'/.gitconfig')
try:
    sss_user = config['user']['name']
    sss_email = config['user']['email']
except Exception as e:
    print("Simple Setup Server (SSS) required your name & email address to track"
          " changes you made under the Git version control")
    print("Simple Setup Server (SSS) will be able to send you daily reports & alerts in "
          "upcoming version")
    print("Simple Setup Server (SSS) will NEVER send your information across")

    sss_user = input("Enter your name: ")
    while sss_user is "":
        print("Name not Valid, Please enter again")
        sss_user = input("Enter your name: ")

    sss_email = input("Enter your email: ")

    while not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$",
                       sss_email):
        print("Invalid email address, please try again")
        sss_email = input("Enter your email: ")

    os.system("git config --global user.name {0}".format(sss_user))
    os.system("git config --global user.email {0}".format(sss_email))

setup(name='sss',
      version='1.0.0',
      description=long_description,
      long_description=long_description,
      classifiers=[],
      keywords='',
      author='',
      author_email='',
      url='https://github.com/serversetup/ServerSetup',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests',
                                      'templates']),
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      install_requires=[
          # Required to build documentation
          # "Sphinx >= 1.0",
          # Required for testing
          # "nose",
          # "coverage",
          # Required to function
          'cement == 2.4',
          'pystache',
          'python-apt',
          'pymysql3 == 0.4',
          'psutil',
          'sh',
          'sqlalchemy',
          ],
      data_files=[('/etc/sss', ['config/sss.conf']),
                  ('/etc/sss/plugins.d', conf),
                  ('/usr/lib/sss/templates', templates),
                  ('/etc/bash_completion.d/',
                   ['config/bash_completion.d/sss_auto.rc']),
                  ('/usr/share/man/man8/', ['docs/sss.8'])],
      setup_requires=[],
      entry_points="""
          [console_scripts]
          sss = sss.cli.main:main
      """,
      namespace_packages=[],
      )
