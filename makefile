.PHONY: upgrade_OS restart stop start scp_private_ini get_private_ini scp_supervisord_conf_to_hosts scp_to_hosts deploy clean

# ssh client must be properly configures with private keys & config to
# be able to directly access any host with 'ssh <host>'...

hosts = bc-veilleuse bc-ui bc-water bc-hq bc-watch bc-power

upgrade_OS:
	echo -e "\x1B[01;93m -= Upgrading each host's OS packages =- \x1B[0m"
	$(foreach host,$(hosts), ssh $(host) "sudo supervisorctl stop all";)
	$(foreach host,$(hosts), ssh -tt $(host) "sudo apt update && sudo apt upgrade -y";)


restart:
	echo -e "\x1B[01;93m -= Restarting each host =- \x1B[0m"
	$(foreach host,$(hosts), ssh $(host) "sudo shutdown -r now";)

stop:
	# 
	echo -e "\x1B[01;93m -= stopping every service on every host using supervisord =- \x1B[0m"
	# stop the services
	$(foreach host,$(hosts), ssh $(host) "sudo supervisorctl stop all";)
	# stop also the docker containers on bc-hq
	-ssh bc-hq "docker stop grafana && docker rm grafana"
	-ssh bc-hq "docker stop influxdb && docker rm influxdb"
	-ssh bc-hq "docker stop nginx && docker rm nginx"

start:
	echo -e "\x1B[01;93m -= starting every service on every host using supervisord =- \x1B[0m"
	# start the docker containers on bc-hq
	ssh bc-hq "sudo chmod a+x docker_influxdb/run_me.sh && docker_influxdb/run_me.sh"
	ssh bc-hq "sudo chmod a+x docker_grafana/run_me.sh && docker_grafana/run_me.sh"
	ssh bc-hq "sudo chmod a+x docker_nginx/run_me.sh && docker_nginx/run_me.sh"
	# start the services
	$(foreach host,$(hosts), ssh $(host) sudo supervisorctl update;)
	$(foreach host,$(hosts), ssh $(host) sudo supervisorctl start all;)

scp_private_ini:
	echo -e "\x1B[01;93m -= copying local private ini files to hosts =- \x1B[0m"
	scp _my_private_ini_files_/logbook.ini bc-watch:~/logbook/
	scp _my_private_ini_files_/pushover_operator.ini bc-watch:~/pushover_operator/
	scp _my_private_ini_files_/SMS_operator.ini bc-watch:~/SMS_operator/
	scp _my_private_ini_files_/BT_scanner.ini bc-veilleuse:~/BT_scanner/

get_private_ini:
	echo -e "\x1B[01;93m -= copying remote private ini file to local dir =- \x1B[0m"
	scp bc-watch:~/logbook/logbook.ini _my_private_ini_files_/
	scp bc-watch:~/pushover_operator/pushover_operator.ini _my_private_ini_files_/
	scp bc-watch:~/SMS_operator/SMS_operator.ini _my_private_ini_files_/
	scp bc-veilleuse:~/BT_scanner/BT_scanner.ini _my_private_ini_files_/

scp_supervisord_conf_to_hosts:
	echo -e "\x1B[01;93m -= copying supervisord conf files to hosts =- \x1B[0m"
	$(foreach host,$(hosts), scp supervisord_conf_files/$(host)_supervisord.conf $(host):~/supervisord.conf;)

scp_to_hosts: stop
	echo -e "\x1B[01;93m -= copying every service source file to hosts =- \x1B[0m"
	# common module to bc-ui
	ssh bc-ui "sudo rm -rf ~/BASECAMP_commons"
	scp -r BASECAMP_commons bc-ui:~/
	# BT_scanner
	ssh bc-veilleuse "sudo rm -rf ~/BT_scanner"
	scp -r BT_scanner bc-veilleuse:~/
	# docker: grafana
	scp docker_grafana/run_me.sh bc-hq:~/docker_grafana
	# docker: influxdb
	scp docker_influxdb/run_me.sh bc-hq:~/docker_influxdb
	# docker: nginx
	ssh bc-hq "sudo rm -rf ~/docker_nginx"
	scp -r docker_nginx bc-hq:~/
	# heater
	ssh bc-power "sudo rm -rf ~/heater"
	scp -r heater bc-power:~/
	# interphone
	ssh bc-ui "sudo rm -rf ~/interphone"
	scp -r interphone bc-ui:~/
	# logbook
	ssh bc-watch "sudo rm -rf ~/logbook"
	scp -r logbook bc-watch:~/
	# PIR_scanner
	ssh bc-ui "sudo rm -rf ~/PIR_scanner"
	scp -r PIR_scanner bc-ui:~/
	# operator
	ssh bc-ui "sudo rm -rf ~/operator"
	scp -r operator bc-ui:~/
	# power
	ssh bc-power "sudo rm -rf ~/power"
	scp -r power bc-power:~/
	# pushover_operator
	ssh bc-watch "sudo rm -rf ~/pushover_operator"
	scp -r pushover_operator bc-watch:~/
	# scheduler
	ssh bc-hq "sudo rm -rf ~/scheduler"
	scp -r scheduler bc-hq:~/
	# SMS_operator
	ssh bc-watch "sudo rm -rf ~/SMS_operator"
	scp -r SMS_operator bc-watch:~/
	# veilleuse
	ssh bc-veilleuse "sudo rm -rf ~/veilleuse"
	scp -r veilleuse bc-veilleuse:~/
	# watchdog_master
	# TODO
	# water
	ssh bc-water "sudo rm -rf ~/water"
	scp -r water bc-water:~/

deploy: stop scp_to_hosts scp_supervisord_conf_to_hosts scp_private_ini start
