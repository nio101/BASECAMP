.DEFAULT_GOAL := mydefault

hosts = bc-veilleuse bc-ui bc-water bc-hq bc-watch bc-power

version:
	# updating version file
	cd ..;./update_version.sh
	cp ../_version_.txt ./
	@cat _version_.txt

test:
	# unit_tests
	pytest

lock:
	@/bin/echo -e "\x1B[01;93m -= locking dependencies to requirements.txt =- \x1B[0m"
	pipenv lock -r > requirements.txt

update:
	@/bin/echo -e "\x1B[01;93m -= Updating dependencies =- \x1B[0m"
	pipenv update

remote_copy:
	@/bin/echo -e "\x1B[01;93m -= Copying to every remote host =- \x1B[0m"
	# basecamp module to every host
	$(foreach host,$(hosts), ssh $(host) "sudo rm -rf ~/basecamp";)
	$(foreach host,$(hosts), scp -r basecamp $(host):~/;)

mydefault:
	# nothing here

.PHONY: test lock update mydefault
