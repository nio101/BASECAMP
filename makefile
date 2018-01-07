.PHONY: upgrade_OS restart stop start scp_private_ini get_private_ini scp_supervisord_conf_to_hosts scp_to_hosts deploy clean

# ssh client must be properly configures with private keys & config to
# be able to directly access any host with 'ssh <host>'...

hosts = bc-veilleuse bc-ui bc-water bc-hq bc-watch bc-power
services = BT_scanner PIR_scanner SMS_operator heater interphone logbook BC_operator power pushover_operator scheduler veilleuse water nightwatch
containers = grafana influxdb nginx

version:
	# updating version file
	@sleep 1
	./update_version.sh
	@cat _version_.txt
	$(foreach service,$(services), scp _version_.txt $(service)/;)


upgrade_OS:
	@/bin/echo -e "\x1B[01;93m -= Upgrading each host's OS packages =- \x1B[0m"
	@sleep 1
	$(foreach host,$(hosts), ssh $(host) "sudo supervisorctl stop all";)
	$(foreach host,$(hosts), ssh -tt $(host) "sudo apt update && sudo apt upgrade -y";)

restart:
	@/bin/echo -e "\x1B[01;93m -= Restarting each host =- \x1B[0m"
	@sleep 1
	$(foreach host,$(hosts), ssh $(host) "sudo shutdown -r now";)

stop:
	@/bin/echo -e "\x1B[01;93m -= stopping every service on every host using supervisord =- \x1B[0m"
	@sleep 1
	# stop the services
	$(foreach host,$(hosts), ssh $(host) "sudo supervisorctl stop all";)
	# stop also the docker containers on bc-hq
	-$(foreach container,$(containers), ssh bc-hq "docker stop $(container) && docker rm $(container)";)

start:
	@/bin/echo -e "\x1B[01;93m -= starting every service on every host using supervisord =- \x1B[0m"
	@sleep 1
	# start the docker containers on bc-hq
	ssh bc-hq "sudo chmod a+x docker_influxdb/run_me.sh && docker_influxdb/run_me.sh"
	ssh bc-hq "sudo chmod a+x docker_grafana/run_me.sh && docker_grafana/run_me.sh"
	ssh bc-hq "sudo chmod a+x docker_nginx/run_me.sh && docker_nginx/run_me.sh"
	# start the services
	$(foreach host,$(hosts), ssh $(host) sudo supervisorctl update;)
	$(foreach host,$(hosts), ssh $(host) sudo supervisorctl start all;)

scp_private_ini:
	@/bin/echo -e "\x1B[01;93m -= copying local private ini files to hosts =- \x1B[0m"
	@sleep 1
	scp _my_private_ini_files_/logbook.ini bc-watch:~/logbook/
	scp _my_private_ini_files_/pushover_operator.ini bc-watch:~/pushover_operator/
	scp _my_private_ini_files_/SMS_operator.ini bc-watch:~/SMS_operator/
	scp _my_private_ini_files_/BT_scanner.ini bc-veilleuse:~/BT_scanner/

get_private_ini:
	@/bin/echo -e "\x1B[01;93m -= copying remote private ini file to local dir =- \x1B[0m"
	@sleep 1
	scp bc-watch:~/logbook/logbook.ini _my_private_ini_files_/
	scp bc-watch:~/pushover_operator/pushover_operator.ini _my_private_ini_files_/
	scp bc-watch:~/SMS_operator/SMS_operator.ini _my_private_ini_files_/
	scp bc-veilleuse:~/BT_scanner/BT_scanner.ini _my_private_ini_files_/

scp_supervisord_conf_to_hosts:
	@/bin/echo -e "\x1B[01;93m -= copying supervisord conf files to hosts =- \x1B[0m"
	@sleep 1
	$(foreach host,$(hosts), scp supervisord_conf_files/$(host)_supervisord.conf $(host):~/supervisord.conf;)

scp_to_hosts: stop
	@/bin/echo -e "\x1B[01;93m -= copying every service source file to hosts =- \x1B[0m"
	@sleep 1
	# common module to bc-ui
	ssh bc-ui "sudo rm -rf ~/BC_commons"
	scp -r BC_commons bc-ui:~/
	# common module to bc-watch
	ssh bc-watch "sudo rm -rf ~/BC_commons"
	scp -r BC_commons bc-watch:~/
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
	# BC_operator
	ssh bc-ui "sudo rm -rf ~/BC_operator"
	scp -r BC_operator bc-ui:~/
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
	# nightwatch
	ssh bc-watch "sudo rm -rf ~/nightwatch"
	scp -r nightwatch bc-watch:~/
	# water
	ssh bc-water "sudo rm -rf ~/water"
	scp -r water bc-water:~/

deploy: version stop scp_to_hosts scp_supervisord_conf_to_hosts scp_private_ini start
	@/bin/echo -e "\x1B[01;93m -= done! =- \x1B[0m"
