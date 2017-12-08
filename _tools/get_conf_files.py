#!/usr/bin/env python3
# coding: utf-8

"""
helper to easily download .ini & supervisord conf files from machines

*** assumes that ssh to destination machines is transparent using .ssh/config ***
"""

import configparser
import subprocess
from colorama import Fore, Style

# =======================================================
# init
print(Fore.GREEN)

# .ini
th_config = configparser.ConfigParser()
th_config.read("basecamp_deploy_info.ini")
private_ini_dir = th_config.get('main', 'private_ini_dir')
# also: getfloat, getint, getboolean

th_config = configparser.ConfigParser()
th_config.read("basecamp_deploy_info.ini")
private_ini_dir = th_config.get('main', 'private_ini_dir')
# also: getfloat, getint, getboolean

machines = {}
for machine in th_config.options("machines"):
    # print(machine, th_config.get('tasks', machine))
    machines[machine] = eval(th_config.get('machines', machine))

# =======================================================
# main loop

print("getting module conf files:")
print("==========================")
for machine in machines.keys():
    print("--- "+machine)
    for package in machines[machine]:
        for ini_file in package["ini"]:
            source_path = machine+":"+package["destination"]+"/"+ini_file
            dest_path = "../"+private_ini_dir
            print("%s:\tcopying %s to %s..." % (package["package"], source_path, dest_path))
            p = subprocess.Popen(["scp", source_path, dest_path])
            sts = p.wait()
    print()

print()
print("getting supervisord conf files:")
print("===============================")
for machine in machines.keys():
    print("--- "+machine)
    source_path = machine+":~/supervisord.conf"
    dest_path = "../"+private_ini_dir+"/"+machine+"_supervisord.conf"
    print("%s:\tcopying %s to %s..." % (machine, source_path, dest_path))
    p = subprocess.Popen(["scp", source_path, dest_path])
    sts = p.wait()
    print()

print(Style.RESET_ALL+"done.")
