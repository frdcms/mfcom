.PHONY: freeze

NAME:=$(shell config.py config.ini general name)
VERSION:=$(shell config.py config.ini general version |sed "s/{{MODULE_VERSION}}/$${MODULE_VERSION}/g")
RELEASE:=1

PREREQ:=.autorestart_includes .autorestart_excludes
DEPLOY:=
ifneq ("$(wildcard python3_virtualenv_sources/requirements-to-freeze.txt)","")
	REQUIREMENTS3:=python3_virtualenv_sources/requirements3.txt
else
	REQUIREMENTS3:=
endif
ifneq ("$(wildcard python3_virtualenv_sources/prerequirements-to-freeze.txt)","")
	REQUIREMENTS3:=python3_virtualenv_sources/prerequirements3.txt $(REQUIREMENTS3)
endif
ifneq ("$(REQUIREMENTS3)","")
	PREREQ+=$(REQUIREMENTS3) python3_virtualenv_sources/src
	DEPLOY+=local/lib/python$(PYTHON3_SHORT_VERSION)/site-packages/requirements3.txt
endif
ifneq ("$(wildcard python2_virtualenv_sources/requirements-to-freeze.txt)","")
	REQUIREMENTS2:=python2_virtualenv_sources/requirements2.txt
else
	REQUIREMENTS2:=
endif
ifneq ("$(wildcard python2_virtualenv_sources/prerequirements-to-freeze.txt)","")
	REQUIREMENTS2:=python2_virtualenv_sources/prerequirements2.txt $(REQUIREMENTS2)
endif
ifneq ("$(REQUIREMENTS2)","")
	PREREQ+=$(REQUIREMENTS2) python2_virtualenv_sources/src
	DEPLOY+=local/lib/python$(PYTHON2_SHORT_VERSION)/site-packages/requirements2.txt
endif
ifneq ("$(wildcard node_sources/package.json)","")
	PREREQ+=node_sources/node_modules
	DEPLOY+=local/lib/node_modules
endif
LAYERS=$(shell cat .layerapi2_dependencies |tr '\n' ',' |sed 's/,$$/\n/')

all: $(PREREQ) custom $(DEPLOY)

.autorestart_includes:
	cp -f $(MFCOM_HOME)/share/plugin_autorestart_includes $@

.autorestart_excludes:
	cp -f $(MFCOM_HOME)/share/plugin_autorestart_excludes $@

clean::
	rm -Rf local *.plugin *.tar.gz python?_virtualenv_sources/*.tmp python?_virtualenv_sources/src python?_virtualenv_sources/freezed_requirements.* python?_virtualenv_sources/tempolayer* tmp_build node_sources/node_modules
	find . -type d -name "__pycache__" -exec rm -Rf {} \; >/dev/null 2>&1 || true

custom::
	@echo "override me" >/dev/null

superclean: clean
	rm -Rf python?_virtualenv_sources/requirements?.txt python?_virtualenv_sources/prerequirements?.txt node_sources/package-lock.json

local/lib/python$(PYTHON3_SHORT_VERSION)/site-packages/requirements3.txt: $(REQUIREMENTS3) python3_virtualenv_sources/src
	_install_plugin_virtualenv $(NAME) $(VERSION) $(RELEASE)
	# to force an autorestart
	touch config.ini

local/lib/python$(PYTHON2_SHORT_VERSION)/site-packages/requirements2.txt: $(REQUIREMENTS2) python2_virtualenv_sources/src
	_install_plugin_virtualenv $(NAME) $(VERSION) $(RELEASE)
	# to force an autorestart
	touch config.ini

python3_virtualenv_sources/requirements3.txt: python3_virtualenv_sources/requirements-to-freeze.txt
	cd python3_virtualenv_sources && layer_wrapper --empty --layers=$(LAYERS) -- freeze_requirements requirements-to-freeze.txt >requirements3.txt

python2_virtualenv_sources/requirements2.txt: python2_virtualenv_sources/requirements-to-freeze.txt
	cd python2_virtualenv_sources && layer_wrapper --empty --layers=$(LAYERS) -- freeze_requirements requirements-to-freeze.txt >requirements2.txt

python3_virtualenv_sources/prerequirements3.txt: python3_virtualenv_sources/prerequirements-to-freeze.txt
	cd python3_virtualenv_sources && layer_wrapper --empty --layers=$(LAYERS) -- freeze_requirements prerequirements-to-freeze.txt >prerequirements3.txt

python2_virtualenv_sources/prerequirements2.txt: python2_virtualenv_sources/prerequirements-to-freeze.txt
	cd python2_virtualenv_sources && layer_wrapper --empty --layers=$(LAYERS) -- freeze_requirements prerequirements-to-freeze.txt >prerequirements2.txt

python3_virtualenv_sources/src: $(REQUIREMENTS3)
	if test -f python3_virtualenv_sources/prerequirements3.txt; then \
	    cd python3_virtualenv_sources && layer_wrapper --empty --layers=$(LAYERS) -- download_compile_requirements prerequirements3.txt; \
	fi
	if test -f python3_virtualenv_sources/requirements3.txt; then \
	    cd python3_virtualenv_sources && layer_wrapper --empty --layers=$(LAYERS) -- download_compile_requirements requirements3.txt; \
	fi

python2_virtualenv_sources/src: $(REQUIREMENTS2)
	if test -f python2_virtualenv_sources/prerequirements2.txt; then \
	    cd python2_virtualenv_sources && layer_wrapper --empty --layers=$(LAYERS) -- download_compile_requirements prerequirements2.txt; \
	fi
	if test -f python2_virtualenv_sources/requirements2.txt; then \
	    cd python2_virtualenv_sources && layer_wrapper --empty --layers=$(LAYERS) -- download_compile_requirements requirements2.txt; \
	fi

release: clean $(PREREQ) custom
	layer_wrapper --empty --layers=$(LAYERS),python3@mfcom -- _plugins.make --show-plugin-path

develop: $(PREREQ) custom $(DEPLOY)
	_plugins.develop $(NAME)

local/lib/node_modules: local/lib/package.json local/lib/package-lock.json node_sources/node_modules
	mkdir -p local/lib
	rm -Rf local/lib/node_modules
	cp -Rf node_sources/node_modules local/lib/
	# to force an autorestart
	touch config.ini

local/lib/package.json: node_sources/package.json
	mkdir -p local/lib
	cp -f $< $@

local/lib/package-lock.json: node_sources/package-lock.json
	mkdir -p local/lib
	cp -f $< $@

node_sources/package-lock.json: node_sources/package.json
	rm -Rf tmp_build
	mkdir -p tmp_build
	cp $< tmp_build/package.json
	cd tmp_build && layer_wrapper --empty --layers=$(LAYERS) -- npm install
	cp -f tmp_build/package-lock.json $@

node_sources/node_modules: node_sources/package-lock.json node_sources/package.json
	rm -Rf tmp_build
	mkdir -p tmp_build
	cp $^ tmp_build/
	cd tmp_build && layer_wrapper --empty --layers=$(LAYERS) -- npm ci install
	rm -Rf $@
	if test -d tmp_build/node_modules; then cp -Rf tmp_build/node_modules node_sources/; else mkdir $@; fi
	rm -Rf tmp_build

freeze:
	if test -d local/lib/node_modules; then rm -Rf node_sources/node_modules; cp -Rf local/lib/node_modules node_sources/; fi
	if test local/lib/package-lock.json; then cp -f local/lib/package-lock.json node_sources/package-lock.json; fi
	if test local/lib/package.json; then cp -f local/lib/package.json node_sources/package.json; fi
	if local/lib/python$(PYTHON3_SHORT_VERSION)/site-packages/requirements3.txt; then echo "ERROR: freeze command is not implemented for python plugins"; fi
	if local/lib/python$(PYTHON2_SHORT_VERSION)/site-packages/requirements2.txt; then echo "ERROR: freeze command is not implemented for python plugins"; fi
