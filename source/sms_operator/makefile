.DEFAULT_GOAL := mydefault

version:
	# updating version file
	cd ..;./update_version.sh
	cp ../_version_.txt ./
	@cat _version_.txt

stop:
	@/bin/echo -e "\x1B[01;93m -= locking dependencies to requirements.txt =- \x1B[0m"
	ssh bc-watch sudo supervisorctl stop sms_operator

start:
	@/bin/echo -e "\x1B[01;93m -= locking dependencies to requirements.txt =- \x1B[0m"
	ssh bc-watch sudo supervisorctl start sms_operator


remote_copy:
	@/bin/echo -e "\x1B[01;93m -= copying to remote machine =- \x1B[0m"
	ssh bc-watch "sudo rm -rf ~/sms_operator"
	cd ..; scp -r sms_operator bc-watch:~/

deploy: version stop remote_copy start
	@/bin/echo -e "\x1B[01;93m -= done! =- \x1B[0m"

mydefault: version
	# done

.PHONY: test lock update mydefault
