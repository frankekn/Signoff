.PHONY: install test typecheck build-web check benchmark demo release

install:
	./install.sh

test:
	python3 scripts/test.py

typecheck:
	npm run typecheck

build-web:
	npm run build:web

check:
	python3 scripts/check_repo.py

benchmark:
	./traction benchmark

demo:
	./scripts/demo.sh

release: typecheck build-web test check
	python3 scripts/build_release.py
