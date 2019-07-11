.PHONY: all clean jslibs

all: KBMS.py KBMS.ini jslibs
	python $^
	
merge:
	git checkout master
	git checkout ponyatov -- KBMS.py KBMS.ini Makefile README.md \
								static templates .gitignore
								
NOW = $(shell date +%d%m%y)
release:
	git tag $(NOW) ; git push -v --tags gh master

jslibs: static/peg.js

static/peg.js:
	wget -c -O $@ https://github.com/pegjs/pegjs/releases/download/v0.10.0/peg-0.10.0.min.js
	
NUM_CPUS = $(shell grep processor /proc/cpuinfo|wc -l)

## build micropython

PREFIX = $(CURDIR)

MICRO_VER = 1.11
MICRO = micropython-$(MICRO_VER)
MICRO_GZ = $(MICRO).tar.xz
micropy: bin/micropython
bin/micropython:
	$(MAKE) tmp/$(MICRO)/README.md
	cd tmp/$(MICRO)/ports/unix ; make axtls ; make -j$(NUM_CPUS) PREFIX=$(PREFIX) install
tmp/$(MICRO)/README.md: tmp/$(MICRO_GZ)
	cd tmp ; xzcat $(MICRO_GZ) | tar x
	touch $@
tmp/$(MICRO_GZ):
	mkdir -p tmp
	wget -c -O $@ http://micropython.org/resources/source/micropython-1.11.tar.xz
	touch $@
	