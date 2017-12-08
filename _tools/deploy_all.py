#!/usr/bin/env python3
# coding: utf-8

"""
helper to easily deploy all modules + custom .ini files & supervisord conf files to machines

*** assumes that ssh to destination machines is transparent using .ssh/config ***
"""

import configparser
import subprocess
from colorama import Fore
import xmlrpc.client
import os.path
import argparse


# =======================================================
# init
print(Fore.GREEN)

# args
parser = argparse.ArgumentParser(description="BASECAMP packages deployment tool")
parser.add_argument("-d", "--deploy", help="stop modules and deploy packages on machines", action="store_true")
parser.add_argument("-r", "--restart", help="restart modules after deployment", action="store_true")
args = parser.parse_args()

# .ini
th_config = configparser.ConfigParser()
th_config.read("basecamp_deploy_info.ini")
private_ini_dir = th_config.get('main', 'private_ini_dir')
xmlrpc_prefix = th_config.get('main', 'xmlrpc_prefix')
xmlrpc_suffix = th_config.get('main', 'xmlrpc_suffix')
# also: getfloat, getint, getboolean

machines = {}
for machine in th_config.options("machines"):
    # print(machine, th_config.get('tasks', machine))
    machines[machine] = eval(th_config.get('machines', machine))

# =======================================================
# main loop

print("stopping services")
print("=================")

for machine in machines.keys():
    # print(machine)
    server = xmlrpc.client.ServerProxy(xmlrpc_prefix+machine+xmlrpc_suffix)
    server_state = server.supervisor.getState()["statename"]
    print("--- "+machine+": "+server.supervisor.getIdentification()+":"+server_state)
    if (server_state != "RUNNING"):
        print(Fore.RED+"!!! ERROR trying to restart supervisord on "+machine+", status="+server_state+" !!!"+Fore.GREEN)
    else:
        server.supervisor.stopAllProcesses(True)
        print("=> all services stopped.")
    """
    all_info = server.supervisor.getAllProcessInfo()
    # print(all_info)
    process_info = {}
    for item in all_info:
        process_info[item["name"]] = item["statename"]
    # print(server.system.listMethods())
    # print(server.system.methodHelp("supervisor.stopProcess"))
    for package in machines[machine]:
        if package["package"] not in process_info.keys():
            print(Fore.YELLOW+"*** WARNING: "+package["package"]+" not found on supervisord's process list ***"+Fore.GREEN)
        else:
            if (process_info[package["package"]] != "RUNNING"):
                print(Fore.YELLOW+"*** WARNING: "+package["package"]+" is not running: status="+process_info[package["package"]]+" ***"+Fore.GREEN)
            else:
                print("stopping "+package["package"])
                if server.supervisor.stopProcess(package["package"], True) is not True:
                    print(Fore.RED+"!!! ERROR trying to stop "+package["package"]+"status="+process_info[package["package"]]+" !!!"+Fore.GREEN)
        # print(server.supervisor.getProcessInfo("interphone"))
        # print(server.supervisor.startProcess("interphone", True))
        # print(server.supervisor.getProcessInfo("interphone"))
        # print(server.supervisor.getAllProcessInfo())
        # print(server.supervisor.getProcessInfo("interphone"))
        """
print()

if (args.deploy):
    print("deploying packages")
    print("==================")
    for machine in machines.keys():
        print("--- "+machine)
        for package in machines[machine]:
            source_path = "../"+package["package"]+"/*"
            dest_path = machine+":"+package["destination"]
            print("%s:\tcopying %s to %s..." % (machine, source_path, dest_path))
            p = subprocess.Popen(["scp", "-r", source_path, dest_path])
            sts = p.wait()

            for ini_file in package["ini"]:
                source_path = "../"+private_ini_dir+"/"+ini_file
                dest_path = machine+":"+package["destination"]
                print("%s:\tcopying %s to %s..." % (machine, source_path, dest_path))
                p = subprocess.Popen(["scp", source_path, dest_path])
                sts = p.wait()
        print()

    print("deploying supervisord conf")
    print("==========================")
    for machine in machines.keys():
        filename = "../"+private_ini_dir+"/"+machine+"_supervisord.conf"
        if os.path.isfile(filename):
            print("found: "+filename)
            dest_path = machine+":~/supervisord.conf"
            source_path = filename
            print("%s:\tcopying %s to %s..." % (machine, source_path, dest_path))
            p = subprocess.Popen(["scp", source_path, dest_path])
            sts = p.wait()
        else:
            print(Fore.YELLOW+"!!! WARNING: not found: "+filename+" !!!"+Fore.GREEN)
        print()

if (args.restart):
    # restarting supervisord also restarts services
    print("restarting supervisord")
    print("======================")
    for machine in machines.keys():
        # print(machine)
        server = xmlrpc.client.ServerProxy(xmlrpc_prefix+machine+xmlrpc_suffix)
        server_state = server.supervisor.getState()["statename"]
        print("--- "+machine+": "+server.supervisor.getIdentification()+":"+server_state)
        if (server_state != "RUNNING"):
            print(Fore.RED+"!!! ERROR trying to restart supervisord on "+machine+", status="+server_state+" !!!"+Fore.GREEN)
        else:
            server.supervisor.restart()
            print("=> all services restarted.")

if (not args.restart) and (not args.deploy):
    print("There's nothing to do !?! Try the -d and -r options...")
print()
print("ALL DONE! :)")

"""
print("starting services")
print("=================")

for machine in machines.keys():
    server = xmlrpc.client.ServerProxy(xmlrpc_prefix+machine+xmlrpc_suffix)
    server_state = server.supervisor.getState()["statename"]
    print("--- "+machine+": "+server.supervisor.getIdentification()+":"+server_state)
    all_info = server.supervisor.getAllProcessInfo()
    # print(all_info)
    process_info = {}
    for item in all_info:
        process_info[item["name"]] = item["statename"]
    # print(server.system.listMethods())
    # print(server.system.methodHelp("supervisor.stopProcess"))
    for package in machines[machine]:
        if package["package"] not in process_info.keys():
            print(Fore.YELLOW+"*** WARNING: "+package["package"]+" not found on supervisord's process list ***"+Fore.GREEN)
        else:
            if (process_info[package["package"]] != "STOPPED"):
                print(Fore.YELLOW+"*** WARNING: "+package["package"]+" is not stopped: status="+process_info[package["package"]]+" ***"+Fore.GREEN)
            else:
                print("starting "+package["package"])
                if server.supervisor.startProcess(package["package"], True) is not True:
                    print(Fore.RED+"!!! ERROR trying to start "+package["package"]+"status="+process_info[package["package"]]+" !!!"+Fore.GREEN)

print(Style.RESET_ALL+"done.")
"""
