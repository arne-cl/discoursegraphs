# a '-' before a shell command causes make to ignore its exit code (errors)

MAZ = data/potsdam-commentary-corpus-2.0.0

neo4j:
	date +"%H:%M:%S"
	-ls $(MAZ)/syntax/*.xml | parallel discoursegraphs -t {} -r $(MAZ)/rst/{/.}.rs3 -c $(MAZ)/connectors/{/.}.xml -m $(MAZ)/coreference/{/.}.mmax -o neo4j
	date +"%H:%M:%S"

install:
	python setup.py install

uninstall:
	yes | pip uninstall discoursegraphs

clean:
	find . -name '*.pyc' -delete
	rm -rf git_stats
	rm -rf build dist src/discoursegraphs.egg-info
	rm -rf docs/_build

kill-delete-restart-neo4j:
	~/bin/neo4j/bin/neo4j stop
	rm -rf ~/bin/neo4j/data/*
	~/bin/neo4j/bin/neo4j start

repopulate-neo4j: kill-delete-restart-neo4j neo4j

# cleans, uninstalls and reinstalls both discoursegraphs and our neonx "fork"
reinstall: clean uninstall install
	cd ~/repos/neonx && make clean && yes | pip uninstall neonx && python setup.py install

frankenstein: reinstall repopulate-neo4j

# runs py.test with coverage.py and creates annoted HTML reports in htmlcov/
coverage:
	py.test --cov=discoursegraphs --cov-report html tests/
