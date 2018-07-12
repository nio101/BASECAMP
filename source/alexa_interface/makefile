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
	ssh bc-ui sudo supervisorctl stop alexa_interface

start:
	@/bin/echo -e "\x1B[01;93m -= starting the service =- \x1B[0m"
	ssh bc-ui sudo supervisorctl start alexa_interface

remote_copy:
	@/bin/echo -e "\x1B[01;93m -= copying to remote machine =- \x1B[0m"
	ssh bc-ui "sudo rm -rf ~/alexa_interface"
	ssh bc-ui "sudo rm -rf ~/basecamp"
	cd ..; scp -r alexa_interface bc-ui:~/
	cd ..; scp -r basecamp bc-ui:~/
	# cd ../..; scp _my_private_ini_files_/alexa_interface.ini bc-ui:~/alexa_interface

clean:
	rm *.log

deploy: clean version stop remote_copy start
	@/bin/echo -e "\x1B[01;93m -= done! =- \x1B[0m"

mydefault:
	# done

.PHONY: test lock update mydefault
