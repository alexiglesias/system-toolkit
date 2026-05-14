.PHONY: help vm-up vm-down vm-ssh test test-unit lint localstack-up localstack-down clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

vm-up:  ## Bring up the Vagrant VM
	vagrant up

vm-down:  ## Halt the Vagrant VM
	vagrant halt

vm-ssh:  ## SSH into the Vagrant VM
	vagrant ssh

vm-destroy:  ## Destroy the Vagrant VM
	vagrant destroy -f

test:  ## Run all tests
	python3 -m pytest tests/ -v

test-unit:  ## Run unit tests (skip ec2 tests if no moto)
	python3 -m pytest tests/test_log_cleaner.py tests/test_log_parser.py -v

lint:  ## Lint bash scripts with shellcheck (if installed)
	@command -v shellcheck >/dev/null 2>&1 && shellcheck bash/*.sh || echo "shellcheck not installed; skipping"

localstack-up:  ## Start LocalStack for boto3 testing
	docker compose up -d
	@echo "LocalStack ready at http://localhost:4566"

localstack-down:  ## Stop LocalStack
	docker compose down

clean:  ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
