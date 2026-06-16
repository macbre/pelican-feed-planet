check:
	# pylint *.py tests/

	# run ./test-server.sh before executing this one
	pytest -o log_cli=true --cov=pelican_planet --cov-report=term --cov-report=xml --cov-fail-under=75 -vv

black:
	black .
