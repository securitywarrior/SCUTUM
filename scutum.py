#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    ╬##################╬
    ##       ##       ##
    ##  #    ##    #  ##
    ##  #    ##    #  ##
    ##  #    ##    #  ##
    ##   #   ##   #   ##
    ##    ## ## ##    ##     ___   __  _  _  ____  _  _  __  __
    ##      ####      ##    / __) / _)( )( )(_  _)( )( )(  \/  )
    ####################    \__ \( (_  )()(   )(   )()(  )    (
    ##      ####      ##    (___/ \__) \__/  (__)  \__/ (_/\/\_)
    ##    ## ## ##    ##
    ##   #   ##   #   ##               ARP Firewall
    ##  #    ##    #  ##
    ##  #    ##    #  ##
    ##  #    ##    #  ##
    ##       ##       ##
    ╬##################╬


Name: SCUTUM Firewall
Author: K4T
Date of Creation: March 8,2017
Last Modified: Sep 27,2017

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt

(C) 2016 - 2017 K4YT3X

Description: SCUTUM is a firewall designed for personal computers that mainly
focuses on ARP defensing

For WICD and Network-Manager

For tutorial please look at the Github Page: https://github.com/K4YT3X/SCUTUM

TODO:
 [x] Create different class for adapter controller
 [x] Create different class for Installer
 [x] Register SCUTUM as a systemd system service
 [x] Change the way configurations are being stored (configparser)
 [ ] Change SCUTUM GUI to adapt systemd
 [ ] Create .deb package
 [ ] Add dynamic inspection?
 [ ] Fix loggin format error
 [ ] Fix options for iptables firewall

"""
from __future__ import print_function
from installer import Installer
from adapter import Adapter
import argparse
import datetime
import os
import urllib.request
import configparser

try:
    import avalon_framework as avalon
except ImportError:
    while True:
        install = input('\033[31m\033[1mAVALON Framework not installed! Install now? [Y/n] \033[0m')
        if len(install) == 0 or install[0].upper() == 'Y':
            try:
                if os.path.isfile('/usr/bin/pip3'):
                    print('Installing using method 1')
                    os.system('pip3 install avalon_framework')
                elif os.path.isfile('/usr/bin/wget'):
                    print('Installing using method 2')
                    os.system('wget -O - https://bootstrap.pypa.io/get-pip.py | python3')
                    os.system('pip3 install avalon_framework')
                else:
                    print('Installing using method 3')
                    # import urllib.request
                    content = urllib.request.urlopen('https://bootstrap.pypa.io/get-pip.py')
                    with open('/tmp/get-pip.py', 'w') as getpip:
                        getpip.write(content.read().decode())
                        getpip.close()
                    os.system('python3 /tmp/get-pip.py')
                    os.system('pip3 install avalon_framework')
                    os.remove('/tmp/get-pip.py')
            except Exception as e:
                print('\033[31mInstallation failed!: ' + str(e))
                print('Please check your Internet connectivity')
                exit(0)
            print('\033[32mInstallation Succeed!\033[0m')
            print('\033[32mPlease restart the program\033[0m')
            exit(0)
        elif install[0].upper() == 'N':
            print('\033[31m\033[1mSCUTUMM requires avalon framework to run!\033[0m')
            print('\033[33mAborting..\033[0m')
            exit(0)
        else:
            print('\033[31m\033[1mInvalid Input!\033[0m')


LOGPATH = '/var/log/scutum.log'
CONFPATH = "/etc/scutum.conf"
VERSION = '2.6.0 beta 1'


# -------------------------------- Functions --------------------------------


def printIcon():
    print(avalon.FM.BD + '     ___   __  _  _  ____  _  _  __  __' + avalon.FM.RST)
    print(avalon.FM.BD + '    / __) / _)( )( )(_  _)( )( )(  \/  )' + avalon.FM.RST)
    print(avalon.FM.BD + '    \__ \( (_  )()(   )(   )()(  )    (' + avalon.FM.RST)
    print(avalon.FM.BD + '    (___/ \__) \__/  (__)  \__/ (_/\/\_)' + avalon.FM.RST)
    print('\n               ARP Firewall')
    spaces = ((32 - len("Version " + VERSION)) // 2) * " "
    print(avalon.FM.BD + "\n" + spaces + '    Version ' + VERSION + '\n' + avalon.FM.RST)


def processArguments():
    """
    This function parses all arguments
    """
    global args
    parser = argparse.ArgumentParser()
    control_group = parser.add_argument_group('Controls')
    control_group.add_argument("--start", help="Enable SCUTUM once before shutdown", action="store_true", default=False)
    control_group.add_argument("--enable", help="Enable SCUTUM", action="store_true", default=False)
    control_group.add_argument("--disable", help="Disable SCUTUM", action="store_true", default=False)
    control_group.add_argument("--status", help="Show SCUTUM current status", action="store_true", default=False)
    # control_group.add_argument("--enablegeneric", help="Enable SCUTUM generic firewall", action="store_true", default=False)
    # control_group.add_argument("--disablegeneric", help="Disnable SCUTUM generic firewall", action="store_true", default=False)
    control_group.add_argument("--reset", help="Disable SCUTUM temporarily before the next connection", action="store_true", default=False)
    control_group.add_argument("--purgelog", help="Purge SCUTUM log file", action="store_true", default=False)
    inst_group = parser.add_argument_group('Installation')
    inst_group.add_argument("--install", help="Install Scutum Automatically", action="store_true", default=False)
    inst_group.add_argument("--uninstall", help="Uninstall Scutum Automatically", action="store_true", default=False)
    inst_group.add_argument("--upgrade", help="Check SCUTUM & AVALON Framework Updates", action="store_true", default=False)
    args = parser.parse_args()


# -------------------------------- Execute --------------------------------

processArguments()
installer = Installer(CONFPATH)
if not (args.enable or args.disable):
        printIcon()

if args.upgrade:
    installer.check_avalon()
    installer.check_version(VERSION)
    exit(0)

try:
    if os.getuid() != 0:  # Arptables requires root
        avalon.error('SCUTUM must be run as root!')
        print(avalon.FG.LGR + 'It needs to control the system firewall so..' + avalon.FM.RST)
        exit(0)
    if not (args.purgelog or args.install or args.uninstall):
        log = open(LOGPATH, 'a+')  # Just for debugging
        log.write(str(datetime.datetime.now()) + ' ---- START ----\n')
        log.write(str(datetime.datetime.now()) + '  UID: ' + str(os.getuid()) + '\n')
        if not os.path.isfile(CONFPATH):
            avalon.error('SCUTUM Config file not found! Please re-install SCUTUM!')
            avalon.warning('Please run "scutum --install" before using it for the first time')
            exit()

        config = configparser.ConfigParser()
        config.read(CONFPATH)
        config.sections()

        interfaces = config["Interfaces"]["interfaces"].split(",")
        if config["Iptables"]["enabled"] == "true":
            iptablesEnabled = True
        elif config["Iptables"]["enabled"] == "false":
            iptablesEnabled = False
        else:
            raise KeyError

        networkControllers = config["networkControllers"]["controllers"]

    if args.install:
        avalon.info('Start Installing SCUTUM...')
        installer.install()
        print('\n' + avalon.FM.BD, end='')
        avalon.info('Installation Complete!')
        avalon.info('SCUTUM service is now enabled on system startup')
        avalon.info('You can now control it with systemd')
        avalon.info("You can also control it manually with \"scutum\" command")
        exit(0)
    elif args.uninstall:
        if avalon.ask('Removal Confirm: ', False):
            installer.removeScutum()
        else:
            avalon.warning('Removal Canceled')
            exit(0)
    elif args.reset:
        log.write(str(datetime.datetime.now()) + ' ---- START ----\n')
        os.system('arptables -P INPUT ACCEPT')
        os.system('arptables --flush')
        avalon.info('RST OK')
        log.write(str(datetime.datetime.now()) + ' RESET OK\n')
    elif args.purgelog:
        os.remove(LOGPATH)
        avalon.info('LOG PURGE OK')
        exit(0)
    elif args.enable or args.disable:
        if args.enable:
            log.write(str(datetime.datetime.now()) + " SCUTUM ENABLED")
            if "wicd" in networkControllers.split(","):
                installer.installNMScripts(config["networkControllers"]["controllers"].split(","))
            if "NetworkManager" in networkControllers.split(","):
                installer.installWicdScripts()
            ifaceobjs = []  # a list to store internet controller objects
            os.system('arptables -P INPUT ACCEPT')  # Accept to get Gateway Cached

            for interface in interfaces:
                interface = Adapter(interface, log)
                ifaceobjs.append(interface)

            for interface in ifaceobjs:
                interface.updateArpTables()
                if iptablesEnabled:
                    interface.iptablesReset()
                    interface.updateIPTables()
            avalon.info('OK')
        elif args.disable:
            log.write(str(datetime.datetime.now()) + " SCUTUM DISABLED")
            installer.removeNMScripts()
            installer.removeWicdScripts()
            os.system('arptables -P INPUT ACCEPT')
            os.system('arptables --flush')
            avalon.info('RST OK')
    else:
        ifaceobjs = []  # a list to store internet controller objects
        os.system('arptables -P INPUT ACCEPT')  # Accept to get Gateway Cached

        for interface in interfaces:
            interface = Adapter(interface, log)
            ifaceobjs.append(interface)

        for interface in ifaceobjs:
            interface.updateArpTables()
            if iptablesEnabled:
                interface.iptablesReset()
                interface.updateIPTables()
        avalon.info('OK')
except KeyboardInterrupt:
    print('\n')
    avalon.warning('^C Pressed! Exiting...')
except KeyError:
    avalon.error('The program configuration file is broken for some reason')
    avalon.error('You should reinstall SCUTUM to repair the configuration file')
except Exception as er:
    avalon.error(str(er))
    if not (args.purgelog or args.install or args.uninstall or os.getuid() != 0):
        log.write(str(datetime.datetime.now()) + ' -!-! ERROR !-!-\n')
        log.write(str(er) + '\n')
finally:
    if not (args.purgelog or args.install or args.uninstall or os.getuid() != 0):
        log.write(str(datetime.datetime.now()) + ' ---- FINISH ----\n\n')
        log.close()
