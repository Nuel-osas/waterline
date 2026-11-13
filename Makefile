# Everything runs on a stock Python 3.9+ with no packages to install and no keys.
PY ?= python3

.PHONY: verify check test build pull serve score all

all: test check

## Re-read a sample of days from public NEAR mainnet, rebuild every number, compare. About a minute.
verify:
	$(PY) -m pipeline.verify

## Same comparison with no network: rebuild every number from the raw data in data/.
check:
	$(PY) -m pipeline.verify --offline

test:
	$(PY) -m unittest discover -s tests

## Rebuild the series, the claims and the dashboard data from data/.
build:
	$(PY) -m pipeline.build
	$(PY) -m pipeline.claims
	$(PY) -m pipeline.score

## Add any missing days from the chain (slow on public nodes; they rate-limit).
pull:
	$(PY) -m pipeline.pull --held

## Open the dashboard at http://localhost:8080
serve:
	$(PY) -m http.server 8080 --directory site

## Score the forward tests in PREREG.md against the readings taken since.
score:
	$(PY) -m pipeline.score
