install:
	pip install -r requirements.txt

load:
	python src/etl/loader.py

test:
	pytest

report:
	python src/etl/validator.py

clean:
	del /Q *.pyc