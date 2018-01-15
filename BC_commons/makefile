.PHONY: test freeze update

test:
	# unit_tests

freeze:
	@/bin/echo -e "\x1B[01;93m -= freezing dependencies to local requirements.txt =- \x1B[0m"
	pipenv lock -r > requirements.txt

update:
	@/bin/echo -e "\x1B[01;93m -= Updating dependencies =- \x1B[0m"
	pipenv update

prepare: update test freeze
	@/bin/echo -e "\x1B[01;93m -= module BC_commons is ready to deploy =- \x1B[0m"
