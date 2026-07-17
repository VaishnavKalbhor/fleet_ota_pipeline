.PHONY: venv install test demo lint-yaml clean

VENV := .venv
PYTHON := $(VENV)/bin/python3

venv:
	python3 -m venv $(VENV)

install: venv
	$(PYTHON) -m pip install \
		-r app/requirements.txt \
		-r update-server/requirements.txt \
		-r vehicle-agent/requirements.txt

test:
	$(PYTHON) -m pytest app/tests update-server/tests vehicle-agent/tests rollout-controller/tests -v

demo:
	$(PYTHON) rollout-controller/demo_rollout.py

lint-yaml:
	$(PYTHON) -c "import yaml, glob; \
[yaml.safe_load_all(open(f)) and print(f, 'OK') for f in glob.glob('deploy/k8s/*.yaml') + glob.glob('.github/workflows/*.yml') + ['docker-compose.yml', 'argocd/application.yaml', 'telemetry/prometheus.yml']]"

clean:
	rm -rf $(VENV) .pytest_cache
	find . -name "__pycache__" -type d -exec rm -rf {} +
