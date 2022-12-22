.PHONY : docs
docs :
	rm -rf docs/build/
	sphinx-autobuild -b html --watch jaffle_shop_generator/ docs/source/ docs/build/

.PHONY : run-checks
run-checks :
	isort --check .
	black --check .
	flake8 .
	mypy .
	pytest -v --color=yes --doctest-modules tests/ jaffle_shop_generator/
