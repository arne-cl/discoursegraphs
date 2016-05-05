# a '-' before a shell command causes make to ignore its exit code (errors)

install:
	pip install -r requirements.txt

uninstall:
	yes | pip uninstall discoursegraphs

clean:
	find . -name '*.pyc' -delete
	find . -name ".ipynb_checkpoints" -type d -exec rm -rf {} \;
	find . -name "__pycache__" -type d -exec rm -rf {} \;
	rm -rf .eggs .cache
	rm -rf git_stats
	rm -rf build dist src/discoursegraphs.egg-info
	rm -rf docs/_build
	rm -rf htmlcov

# cleans, uninstalls and reinstalls discoursegraphs
reinstall: uninstall clean install


# runs py.test with coverage.py and creates annoted HTML reports in htmlcov/
coverage:
	py.test --cov=discoursegraphs --cov-report html tests/
