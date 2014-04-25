# a '-' before a shell command causes make to ignore its exit code (errors)

MAZ = ~/repos/pcc-annis-merged/maz176

all:
	mkdir -p /tmp/dg
	date +"%H:%M:%S"
	-ls $(MAZ)/syntax/*.xml | parallel ~/repos/discoursegraphs/src/discoursegraphs/merging.py {} $(MAZ)/rst/{/.}.rs3 $(MAZ)/anaphora/tosik/das/{/.}.txt /tmp/dg/{/.}.dot
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
