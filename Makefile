# Everything runs on a stock Python 3.9+ with no packages to install and no keys.
PY ?= python3

.PHONY: verify check test build pull serve score model trace audit context all

all: test check

## Re-read a sample of days from public NEAR mainnet, rebuild every number, compare. One to three minutes.
verify:
	$(PY) -m pipeline.verify

## Same comparison with no network: rebuild every number from data/ in memory. Writes nothing.
check:
	$(PY) -m pipeline.verify --offline

test:
	$(PY) -m unittest discover -s tests

## Rebuild the series, the claims and the dashboard data from data/.
build:
	$(PY) -m pipeline.build
	$(PY) -m pipeline.claims
	$(PY) -m pipeline.score
	$(PY) -m pipeline.score_audit

## Refetch the token list, the quoted figures, the supply headers and the custody facts.
context:
	$(PY) -m pipeline.context

## Add any missing days from the chain (slow on public nodes; they rate-limit).
pull:
	$(PY) -m pipeline.pull --held
	$(PY) -m pipeline.audit --pull

## Open the dashboard at http://localhost:8080
serve:
	$(PY) -m http.server 8080 --directory site

## Score the forward tests in PREREG.md against the readings taken since.
score:
	$(PY) -m pipeline.score
	$(PY) -m pipeline.score_audit

## Audit the 20 largest tokens at the latest final block: credited by intents.near against held, token by token.
audit:
	$(PY) -m pipeline.audit --now

## Find, from balances alone, the largest single move of NEAR into the treasury before the 25 September reading,
## and print the receipt behind it. About 25 requests, about a minute.
trace:
	$(PY) -m pipeline.trace 2026-09-25 --top 1

## Replay the float's past daily changes forward and count how often the long-dated readings hold. Seeded.
model:
	$(PY) -m pipeline.model
