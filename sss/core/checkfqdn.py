from sss.core.shellexec import SSSShellExec
from sss.core.variables import SSSVariables
import os

def check_fqdn(self, sss_host):
    """FQDN check with Simple Setup Server, for mail server hostname must be FQDN"""
    # sss_host=os.popen("hostname -f | tr -d '\n'").read()
    if '.' in sss_host:
        SSSVariables.sss_fqdn = SSS_host
        with open('/etc/hostname', encoding='utf-8', mode='w') as hostfile:
            hostfile.write(sss_host)

        SSSShellExec.cmd_exec(self, "sed -i \"1i\\127.0.0.1 {0}\" /etc/hosts"
                                   .format(sss_host))
        if SSSVariables.sss_platform_distro == 'debian':
            SSSShellExec.cmd_exec(self, "/etc/init.d/hostname.sh start")
        else:
            SSSShellExec.cmd_exec(self, "service hostname restart")

    else:
        sss_host = input("Enter hostname [fqdn]:")
        check_fqdn(self, sss_host)
