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
	ssh bc-veilleuse sudo supervisorctl stop veilleuse

start:
	@/bin/echo -e "\x1B[01;93m -= starting the service =- \x1B[0m"
	ssh bc-veilleuse sudo supervisorctl start veilleuse

remote_copy:
	@/bin/echo -e "\x1B[01;93m -= copying to remote machine =- \x1B[0m"
	ssh bc-veilleuse "sudo rm -rf ~/veilleuse"
	ssh bc-veilleuse "sudo rm -rf ~/basecamp"
	cd ..; scp -r veilleuse bc-veilleuse:~/
	cd ..; scp -r basecamp bc-veilleuse:~/
	# cd ../..; scp _my_private_ini_files_/veilleuse.ini bc-veilleuse:~/veilleuse

clean:
	rm *.log

deploy: clean version stop remote_copy start
	@/bin/echo -e "\x1B[01;93m -= done! =- \x1B[0m"

mydefault:
	# done

.PHONY: test lock update mydefault
