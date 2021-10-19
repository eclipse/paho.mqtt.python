# Set DESTDIR if it isn't given
DESTDIR?=/
PYTHON?=python3

.PHONY : all clean clean-build clean-pyc clean-test install test upload

all :
	$(PYTHON) ./setup.py build

install : all
	$(PYTHON) ./setup.py install --root=${DESTDIR}

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts


clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

test :
	$(PYTHON) setup.py test
	$(MAKE) -C test test

upload : test
	$(PYTHON) ./setup.py sdist upload
