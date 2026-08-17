.PHONY: load ratios test report dashboard api clean

load:
	python -m src.etl.loader

ratios:
	python -m src.analytics.ratios

test:
	python -m pytest tests/ --html=reports/pytest_report.html

report:
	python -m src.reports.batch_generator

dashboard:
	python -m streamlit run src/dashboard/app.py --server.port=8501

api:
	python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload

clean:
	rm -rf reports/pytest_report.html
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
