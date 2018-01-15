.DEFAULT_GOAL := mydefault

test:
	# unit_tests
	pytest

lock:
	@/bin/echo -e "\x1B[01;93m -= locking dependencies to requirements.txt =- \x1B[0m"
	pipenv lock -r > requirements.txt

update:
	@/bin/echo -e "\x1B[01;93m -= Updating dependencies =- \x1B[0m"
	pipenv update

mydefault: update test lock
	@/bin/echo -e "\x1B[01;93m -= package basecamp is ready to deploy =- \x1B[0m"

.PHONY: test lock update mydefault
