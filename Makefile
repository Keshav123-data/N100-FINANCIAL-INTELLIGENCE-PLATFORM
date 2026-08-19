install:
	pip install -r requirements.txt

load:
	python Script/ETL/loader.py

test:
	pytest

report:
	python Script/ETL/validator.py

clean:
	del /Q *.pyc