#!/usr/bin/env python
# coding: utf-8

"""
helper to easily download .ini files from machines

*** assumes that ssh to destination machines is transparent using .ssh/config ***

(python2/python3 compatible)
"""


import configparser
import subprocess
import os
import time


# =======================================================
# init

# .ini
th_config = configparser.ConfigParser()
th_config.read("basecamp_deploy_info.ini")
private_ini_dir = th_config.get('main', 'private_ini_dir')
# also: getfloat, getint, getboolean

packages = {}
for package in th_config.options("packages"):
    # print(machine, th_config.get('tasks', machine))
    packages[package] = eval(th_config.get('packages', package))

# =======================================================
# main loop

for package in packages.keys():
    for ini_file in packages[package]["ini"]:
        print("\n%s:\tcopying %s to %s..." % (package, packages[package]["machine"]+":"+packages[package]["destination"]+"/"+ini_file, "../"+private_ini_dir))
        p = subprocess.Popen(["scp", packages[package]["machine"]+":"+packages[package]["destination"]+"/"+ini_file, "../"+private_ini_dir])
        sts = p.wait()

"""
client = scp.Client(host=host, user=user, keyfile=keyfile)
# or
client = scp.Client(host=host, user=user)
client.use_system_keys()
# or
client = scp.Client(host=host, user=user, password=password)

# and then
client.transfer('/etc/local/filename', '/etc/remote/filename')
"""

print("done.")
