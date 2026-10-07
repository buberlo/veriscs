# Local build, checker, and benchmark. There is no GitHub Actions workflow.
#
#   make deps      fetch mathlib at the pinned commit and its olean cache
#   make build     native executable .lake/build/bin/veriscs
#   make axioms    print axioms of answer_spec and answer_implementation
#   make test      Python unit tests (no Lean binary required)
#   make check     run veriscs on the small fixtures and the Python checker
#   make bench     timed comparison against greedy merge and exact optimum
#
# `make deps` is the slow download. Repeat `make build` after it.

BIN := .lake/build/bin/veriscs
export PATH := $(HOME)/.elan/bin:$(PATH)

.PHONY: deps build axioms test check bench

deps:
	lake update
	lake exe cache get

build:
	lake build veriscs

axioms:
	lake env lean VeriSCS/Axioms.lean

test:
	python3 tools/test_scs.py

check: $(BIN)
	$(BIN) --roundtrip tests/instances/ab_bc.txt | cmp - tests/instances/ab_bc.txt
	$(BIN) --stats tests/instances/one.txt | python3 tools/checker.py tests/instances/one.txt -
	$(BIN) --stats tests/instances/ab_bc.txt | python3 tools/checker.py tests/instances/ab_bc.txt -
	$(BIN) --stats tests/instances/contained.txt | python3 tools/checker.py tests/instances/contained.txt -
	$(BIN) --stats tests/instances/ab_ba.txt | python3 tools/checker.py tests/instances/ab_ba.txt -

bench: $(BIN)
	python3 tools/benchmark.py --bin $(BIN) --timeout 30 --out BENCHMARK.md
