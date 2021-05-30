.DEFAULT_GOAL := mydefault

version:
	# updating version file
	cd ..;./update_version.sh
	cp ../_version_.txt ./
	@cat _version_.txt
	cd ../basecamp;make version

test:
	# unit_tests
	pytest

stop:
	@/bin/echo -e "\x1B[01;93m -= stopping the service =- \x1B[0m"
	ssh bc-watch sudo supervisorctl stop logbook

start:
	@/bin/echo -e "\x1B[01;93m -= starting the service =- \x1B[0m"
	ssh bc-watch sudo supervisorctl start logbook

remote_copy:
	@/bin/echo -e "\x1B[01;93m -= copying to remote machine =- \x1B[0m"
	ssh bc-watch "sudo rm -rf ~/logbook"
	ssh bc-watch "sudo rm -rf ~/basecamp"
	cd ..; scp -r logbook bc-watch:~/
	cd ..; scp -r basecamp bc-watch:~/
	cd ../..; scp _my_private_ini_files_/logbook.ini bc-watch:~/logbook

clean:
	rm *.log

deploy: clean version stop remote_copy start
	@/bin/echo -e "\x1B[01;93m -= done! =- \x1B[0m"

mydefault:
	# done

.PHONY: test lock update mydefault
