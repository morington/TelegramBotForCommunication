# ===============================
# Cross-platform Makefile (Linux + Windows cmd/powershell)
# ===============================

ENV_FILE ?= .env
NETWORK ?= my_network

# Считываем .env, если существует
ifeq ($(wildcard $(ENV_FILE)), $(ENV_FILE))
	include $(ENV_FILE)
else
	$(warning "$(ENV_FILE) not found. Env variables not loaded.")
endif

all: build

help:
	@echo "Available commands:"
	@echo "   make help                 - Show this help"
	@echo "   make                      - Default: run all"
	@echo "   make dev-build            - Start in development mode"
	@echo "   make build                - Start all containers"
	@echo "   make down                 - Stop all containers"
	@echo "   make restart              - Restart containers"
	@echo "   make eenv                 - Encode .env"
	@echo "   make denv                 - Decode .env"

eenv:
	python scripts/enc.py encode -i .env

denv:
	@python -c "import os; key = input('Enter encoded key: '); os.system(f'python scripts/enc.py decode {key} -o .env')"

dev-build:
	@echo "Starting in development mode..."
	docker compose up -d PostgreSQLService_9RYAQ5 RedisService_9RYAQ5 NatsServer_9RYAQ5

build:
	@echo "Starting all containers..."
	docker compose up -d
	@echo "Done!"

down:
	@echo "Stopping all containers..."
	docker compose down
	@echo "Stopped."

restart:
	$(MAKE) down
	$(MAKE) build

dev-restart:
	$(MAKE) down
	$(MAKE) dev-build

clean:
	docker compose down
	-docker network rm $(NETWORK)
