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

distclean: ;

q2_composition/_ancombc2_visualizer/dist:
	cd q2_composition/_ancombc2_visualizer/ && \
	npm install && \
	npm run build

ancombc2-visualizer: q2_composition/_ancombc2_visualizer/dist
