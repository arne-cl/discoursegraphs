# a '-' before a shell command causes make to ignore its exit code (errors)

MAZ = ~/repos/pcc-annis-merged/maz176

merge-only:
	date +"%H:%M:%S"
	-ls $(MAZ)/syntax/*.xml | parallel ~/repos/discoursegraphs/src/discoursegraphs/merging.py -t {} -r $(MAZ)/rst/{/.}.rs3 -a $(MAZ)/anaphora/tosik/das/{/.}.txt -o no-output
	date +"%H:%M:%S"


neo4j:
	date +"%H:%M:%S"
	-ls $(MAZ)/syntax/*.xml | parallel ~/repos/discoursegraphs/src/discoursegraphs/merging.py -t {} -r $(MAZ)/rst/{/.}.rs3 -a $(MAZ)/anaphora/tosik/das/{/.}.txt -o neo4j
	date +"%H:%M:%S"

all:
	mkdir -p /tmp/dg
	date +"%H:%M:%S"
	-ls $(MAZ)/syntax/*.xml | parallel ~/repos/discoursegraphs/src/discoursegraphs/merging.py -t {} -r $(MAZ)/rst/{/.}.rs3 -a $(MAZ)/anaphora/tosik/das/{/.}.txt /tmp/dg/{/.}.dot
	date +"%H:%M:%S"

gitstats:
	git_stats generate --silent --output=/tmp/dg
	firefox /tmp/dg/lines/by_date.html

show: all
	ls /tmp/dg/*.dot | parallel dot -Tsvg {} -o {.}.svg

install:
	python setup.py install

uninstall:
	yes | pip uninstall discoursegraphs

clean:
	find . -name *.pyc -delete
	rm -rf git_stats /tmp/dg
	rm -rf build dist src/discoursegraphs.egg-info

kill-delete-restart-neo4j:
	~/bin/neo4j/bin/neo4j stop
	rm -rf ~/bin/neo4j/data/*
	~/bin/neo4j/bin/neo4j start

repopulate-neo4j: kill-delete-restart-neo4j neo4j

reinstall: clean uninstall install
	cd ~/repos/neonx && make clean && yes | pip uninstall neonx && python setup.py install
