install:
	pip install -r requirements.txt

load:
	python Script/ETL/loader.py

test:
	python Script/generate_deliverables.py --test-report

report:
	python Script/generate_deliverables.py
	python Script/ETL/validator.py

clean:
	del /Q *.pyc