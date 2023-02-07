SOURCE?=Mrk421

all: build/lst1-$(SOURCE)-runlist-checked.csv

archive: build/lst1-dl1-datachecks-$(SOURCE).tar.gz

data:
	mkdir -p $@

data/tar-%.txt: build/lst1-dl1-datachecks-%.tar.gz | data
	tar xzf $< --strip-components=8 -C data

build/lst1-dl1-datachecks-%.tar.gz: build/lst1-dl1-datachecks-%.txt
	echo "Done" > build/tar.txt
	tar czf $@ build/tar.txt -T $<
	rm build/tar.txt

build/lst1-dl1-datachecks-%.txt: scripts/list-all-datachecks.py build/lst1-%-runlist.csv
	python $^ $@

build/lst1-%-runlist-checked.csv: scripts/data-check.py build/lst1-%-runlist.csv data/tar-%.txt
	python scripts/data-check.py build/lst1-$*-runlist.csv $@ $*

build:
	mkdir -p $@

build/lst1-runlist.html: lst1-authentication.json | build
	https --check-status \
		https://lst1.iac.es/datacheck/lstosa/LST_source_catalog.html \
		--session-read-only=./$< \
		-o $@ || rm -f $@

build/lst1-%-runlist.csv: scripts/select-data.py build/lst1-runlist.html
	python $^ $@ $*

clean:
	rm -rf build

.PHONY: all archive clean
