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
	@echo "   make revision name=msg   - Create alembic revision"
	@echo "   make migrate              - Run all migrations"

eenv:
	python scripts/enc.py encode -i .env

denv:
	@python -c "import os; key = input('Enter encoded key: '); os.system(f'python scripts/enc.py decode {key} -o .env')"

dev-build:
	@echo "Starting in development mode..."
	$(MAKE) _create_network
	docker compose up -d PostgreSQLService_9RYAQ5 RedisService_9RYAQ5 NatsServer_9RYAQ5

build:
	$(MAKE) _create_network
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

_create_network:
	@echo "Creating Docker network if not exists..."
	@docker network inspect $(NETWORK) > /dev/null 2>&1 || docker network create $(NETWORK)

clean:
	docker compose down
	-docker network rm $(NETWORK)

revision:
	alembic revision -m "$(name)" --autogenerate

migrate:
	@python -c "import os; resp = input('WARNING: Verify all alembic migrations (y/N): '); os.system('alembic upgrade head') if resp.lower() == 'y' else print('Migration cancelled.')"
