.PHONY: all lint test test-cov install dev clean distclean

PYTHON ?= python

all: ancombc2-visualizer;

lint:
	q2lint
	flake8

test: all
	py.test

test-cov: all
	py.test --cov=q2_composition

install: all
	$(PYTHON) -m pip install -v .

dev: all
	pip install -e .

clean: distclean
	rm -rf q2_composition/_da_barplot/node_modules

distclean:
	rm -rf q2_composition/_da_barplot/dist/

q2_composition/_da_barplot/dist:
	cd q2_composition/_da_barplot/ && \
	npm install && \
	npm run build

ancombc2-visualizer: q2_composition/_da_barplot/dist
