.PHONY : docs
docs :
	rm -rf docs/build/
	sphinx-autobuild -b html --watch jafgen/ docs/source/ docs/build/

.PHONY : run-checks
run-checks :
	isort --check .
	black --check .
	flake8 .
	mypy .
	pytest -v --color=yes --doctest-modules tests/ jafgen/
