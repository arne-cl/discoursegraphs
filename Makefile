# a '-' before a shell command causes make to ignore its exit code (errors)

install:
	python setup.py install

uninstall:
	yes | pip uninstall discoursegraphs

clean:
	find . -name '*.pyc' -delete
	rm -rf git_stats
	rm -rf build dist src/discoursegraphs.egg-info
	rm -rf docs/_build
	rm -rf htmlcov

# cleans, uninstalls and reinstalls discoursegraphs
reinstall: clean uninstall
	python setup.py install

# runs py.test with coverage.py and creates annoted HTML reports in htmlcov/
coverage:
	py.test --cov=discoursegraphs --cov-report html tests/
