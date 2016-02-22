"""Simple Setup Server SWAP creation"""
from sss.core.variables import SSSVariables
from sss.core.shellexec import SSSShellExec
from sss.core.fileutils import SSSFileUtils
from sss.core.aptget import SSSAptGet
from sss.core.logging import Log
import os

class SSSSwap():
    """Manage Swap"""

    def __init__():
        """Initialize """
        pass

    def add(self):
        """Swap addition with SimpleSetupServer"""
        if SSSVariables.sss_ram < 512:
            if SSSVariables.sss_swap < 1000:
                Log.info(self, "Adding SWAP file, please wait...")

                # Install dphys-swapfile
                SSSAptGet.update(self)
                SSSAptGet.install(self, ["dphys-swapfile"])
                # Stop service
                SSSShellExec.cmd_exec(self, "service dphys-swapfile stop")
                # Remove Default swap created
                SSSShellExec.cmd_exec(self, "/sbin/dphys-swapfile uninstall")

                # Modify Swap configuration
                if os.path.isfile("/etc/dphys-swapfile"):
                    SSSFileUtils.searchreplace(self, "/etc/dphys-swapfile",
                                              "#CONF_SWAPFILE=/var/swap",
                                              "CONF_SWAPFILE=/sss-swapfile")
                    SSSFileUtils.searchreplace(self,  "/etc/dphys-swapfile",
                                              "#CONF_MAXSWAP=2048",
                                              "CONF_MAXSWAP=1024")
                    SSSFileUtils.searchreplace(self,  "/etc/dphys-swapfile",
                                              "#CONF_SWAPSIZE=",
                                              "CONF_SWAPSIZE=1024")
                else:
                    with open("/etc/dphys-swapfile", 'w') as conffile:
                        conffile.write("CONF_SWAPFILE=/sss-swapfile\n"
                                       "CONF_SWAPSIZE=1024\n"
                                       "CONF_MAXSWAP=1024\n")
                # Create swap file
                SSSShellExec.cmd_exec(self, "service dphys-swapfile start")
