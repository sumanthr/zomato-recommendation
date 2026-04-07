PYTHON ?= python

.PHONY: test phase1 phase3 api

test:
	$(PYTHON) -m pytest

phase1:
	$(PYTHON) -m src.phases.phase_1.pipeline

phase3:
	$(PYTHON) -m src.phases.phase_3.pipeline --input-json '{"location":"Bangalore","budget":"medium","cuisine":"Italian","minimum_rating":4.0,"top_k":5}'

api:
	$(PYTHON) -m uvicorn src.phases.phase_4.api:app --reload
