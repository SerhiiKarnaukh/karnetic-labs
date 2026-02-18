# Load variables from .env
include .env
export

run:
	docker-compose up -d

build:
	docker-compose up -d --build && docker image prune -f

test:
	docker-compose run --rm app sh -c "\
		flake8 && \
		DJANGO_SETTINGS_MODULE=portfolio.settings_test \
		coverage run manage.py test && \
		coverage report && \
		coverage html"
	docker-compose down

stop:
	@echo "💾 Creating a database backup..."
	docker-compose exec db pg_dump -U $(SQL_USER) $(SQL_DATABASE) > temp/db_backup.sql
	@echo "⛔ Stopping docker-compose..."
	docker-compose down
	$(MAKE) clean

backup:
	@echo "💾 Start backup..."
	docker-compose up -d
	docker-compose exec db dropdb -U $(SQL_USER) $(SQL_DATABASE)
	docker-compose exec db createdb -U $(SQL_USER) $(SQL_DATABASE)
	docker-compose exec -T db psql -U $(SQL_USER) $(SQL_DATABASE) < temp/db_backup.sql

migrate:
	docker-compose run --rm app sh -c "python manage.py makemigrations"
	docker-compose run --rm app sh -c "python manage.py migrate"

super:
	docker-compose run --rm app sh -c "python manage.py createsuperuser"

clean:
	docker image prune -f
	docker volume prune -f
	docker builder prune --all -f

# before install Poetry
# curl -sSL https://install.python-poetry.org -o install-poetry.py
# python install-poetry.py
# poetry self add poetry-plugin-export
update:
	rm -f pyproject.toml poetry.lock
	poetry init --no-interaction --name project --quiet
	sed -i 's/python = ">=3.12"/python = ">=3.12,<4.0"/' pyproject.toml
	cat requirements.txt | cut -d= -f1 | xargs -n1 poetry add
	poetry update
	poetry show --only=main --tree | grep -E '^[a-zA-Z0-9_\-]+' | awk '{print $$1"=="$$2}' > requirements.txt
	rm -f pyproject.toml poetry.lock
	$(MAKE) update_front_taberna
	$(MAKE) update_front_core
	docker-compose build
	$(MAKE) test
	$(MAKE) clean

update_front_taberna:
	cd portfolio/apps/taberna_product/_dev && \
	rm -rf node_modules && \
	rm -f package-lock.json && \
	ncu && \
	ncu -u && \
	npm install && \
	npm run b && \
	rm -rf node_modules && \
	cd /d/projects/karnetic-labs

update_front_core:
	cd portfolio/apps/core/_dev && \
	rm -rf node_modules && \
	rm -f package-lock.json && \
	ncu && \
	ncu -u && \
	npm install && \
	npm run b && \
	rm -rf node_modules && \
	cd /d/projects/karnetic-labs

sync-f1:
	docker-compose -f docker-compose.deploy.yml run --rm app sh -c \
	"python manage.py sync_f1_sessions --year 2023 && \
	 python manage.py sync_f1_sessions --year 2024 && \
	 python manage.py sync_f1_sessions --year 2025"

########################For Remote Host Makefile##############################
#When making changes to this block, you must first run:
#1.connect to your server with ssh
#2. git pull origin|development command on the server
#3. make prod|dev command on the server
clean-orphaned-safe:
	@echo "🔍 Cleaning orphaned Docker layers..."
	@docker images -aq | xargs -I {} docker inspect {} 2>/dev/null | grep -oP '(?<=/var/lib/docker/overlay2/)[a-z0-9]+(?=/diff)' | sort -u > /tmp/keep_layers.txt || true
	@sudo ls /var/lib/docker/overlay2/ | while read dir; do \
		if ! grep -q "^$$dir$$" /tmp/keep_layers.txt && [ "$$dir" != "l" ]; then \
			sudo rm -rf "/var/lib/docker/overlay2/$$dir" 2>/dev/null || true; \
		fi \
	done
	@echo "✅ Orphaned layers cleanup complete"

clean-docker:
	docker system prune -a --volumes -f
	docker builder prune -af
	sudo journalctl --vacuum-size=100M


build-front-end:
	cd portfolio/apps/taberna_product/_dev && \
	rm -rf node_modules && \
	npm install && \
	NODE_OPTIONS="--max-old-space-size=1024" npm run b -- --progress=profile && \
	rm -rf node_modules && \
	cd ~/karnetic-labs &&\
	cd portfolio/apps/core/_dev &&\
	rm -rf node_modules && \
	npm install && \
	NODE_OPTIONS="--max-old-space-size=1024" npm run b -- --progress=profile && \
	rm -rf node_modules && \
	cd ~/karnetic-labs

deploy:
	docker-compose -f docker-compose.deploy.yml down
	$(MAKE) build-front-end
	docker-compose -f docker-compose.deploy.yml build
	docker-compose -f docker-compose.deploy.yml run --rm app sh -c "python manage.py makemigrations"
	docker-compose -f docker-compose.deploy.yml run --rm app sh -c "python manage.py migrate"
	$(MAKE) clean-orphaned-safe
	docker-compose -f docker-compose.deploy.yml up -d
	$(MAKE) clean-docker

prod:
	git pull origin
	$(MAKE) deploy

dev:
	git pull origin development
	$(MAKE) deploy

proxy:
	docker-compose -f docker-compose.deploy.yml down
	docker volume rm $$(docker volume ls -qf name=certbot-web)
	docker volume rm $$(docker volume ls -qf name=proxy-dhparams)
	docker volume rm $$(docker volume ls -qf name=certbot-certs)
	docker-compose -f docker-compose.deploy.yml run --rm certbot /opt/certify-init.sh
	docker-compose -f docker-compose.deploy.yml down
	docker-compose -f docker-compose.deploy.yml build
	docker-compose -f docker-compose.deploy.yml up -d
	docker system prune -a --volumes -f

backup-host:
	docker-compose -f docker-compose.deploy.yml exec db pg_dump -U $(SQL_USER) $(SQL_DATABASE) > ../db_backup.sql
	docker run --rm \
	-v karnetic-labs_static-data:/data \
	-v /home/ec2-user:/backup \
	alpine tar -czf /backup/vol_web_backup.tar.gz -C /data .

db-backup-restore:
	docker-compose -f docker-compose.deploy.yml exec db dropdb -U $(SQL_USER) $(SQL_DATABASE)
	docker-compose -f docker-compose.deploy.yml exec db createdb -U $(SQL_USER) $(SQL_DATABASE)
	docker-compose -f docker-compose.deploy.yml exec -T db psql -U $(SQL_USER) $(SQL_DATABASE) < ../db_backup.sql

media-backup-restore:
	docker run --rm \
	-v karnetic-labs_static-data:/data \
	-v /home/ec2-user:/backup \
	alpine sh -c "cd /data && tar -xzf /backup/vol_web_backup.tar.gz"

restore:
	$(MAKE) db-backup-restore
	$(MAKE) media-backup-restore

# PostgreSQL Update Steps:
# 1. Backup: make backup-host
# 2. Update: local image: postgres:version-alpine
# 3. Push to repo (GitHub Action will likely fail, but image pull is what matters)
# 4. SSH to server: make postgres
# 5. On 18 postgres you need to add - PGDATA=/var/lib/postgresql/data/pgdata
postgres:
	docker-compose -f docker-compose.deploy.yml down
	docker volume rm $$(docker volume ls -qf name=postgres-data)
	docker volume rm $$(docker volume ls -qf name=redisdata)
	$(MAKE) deploy
	$(MAKE) db-backup-restore
