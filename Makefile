# a '-' before a shell command causes make to ignore its exit code (errors)

MAZ = ~/repos/pcc-annis-merged/maz176

all:
	mkdir -p /tmp/dg
	date +"%H:%M:%S"
	-ls $(MAZ)/syntax/*.xml | parallel discoursegraphs -t {} -r $(MAZ)/rst/{/.}.rs3 -a $(MAZ)/anaphora/tosik/das/{/.}.txt /tmp/dg/{/.}.dot
	date +"%H:%M:%S"

show: all
	ls /tmp/dg/*.dot | parallel dot -Tsvg {} -o {.}.svg

merge-only:
	date +"%H:%M:%S"
	-ls $(MAZ)/syntax/*.xml | parallel discoursegraphs -t {} -r $(MAZ)/rst/{/.}.rs3 -a $(MAZ)/anaphora/tosik/das/{/.}.txt -c $(MAZ)/connectors/{/.}.xml -m $(MAZ)/coreference/{/.}.mmax -o no-output
	date +"%H:%M:%S"

exmaralda:
	-ls $(MAZ)/anaphora/tosik/das/*.txt | parallel discoursegraphs -a {} -c $(MAZ)/connectors/{/.}.xml -m $(MAZ)/coreference/{/.}.mmax -r $(MAZ)/rst/{/.}.rs3 -t $(MAZ)/syntax/{/.}.xml -o exmaralda /tmp/dg/{/.}.exb

neo4j:
	date +"%H:%M:%S"
	-ls $(MAZ)/syntax/*.xml | parallel discoursegraphs -t {} -r $(MAZ)/rst/{/.}.rs3 -a $(MAZ)/anaphora/tosik/das/{/.}.txt -o neo4j
	date +"%H:%M:%S"

gitstats:
	git_stats generate --silent --output=/tmp/dg
	firefox /tmp/dg/lines/by_date.html

install:
	python setup.py install

uninstall:
	yes | pip uninstall discoursegraphs

clean:
	find . -name *.pyc -delete
	rm -rf git_stats /tmp/dg
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

lint:
	flake8 src

frankenstein: reinstall repopulate-neo4j
