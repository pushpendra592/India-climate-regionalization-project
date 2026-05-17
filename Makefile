.PHONY: setup collect preprocess cluster all clean

setup:
	pip install -r requirements.txt
	mkdir -p data/raw/nasa_power
	mkdir -p data/interim data/processed data/external
	mkdir -p outputs/figures outputs/reports outputs/models outputs/tables

collect:
	python pipelines/data_pipeline.py --step collect

preprocess:
	python pipelines/data_pipeline.py --step preprocess

cluster:
	python pipelines/clustering_pipeline.py

insights:
	python pipelines/insight_pipeline.py

all: collect preprocess cluster insights

clean:
	rm -rf data/interim/* data/processed/* outputs/*

test:
	pytest tests/ -v
