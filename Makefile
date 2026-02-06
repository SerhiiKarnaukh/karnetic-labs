# Load variables from .env
include .env
export

run:
	docker-compose up -d

build:
	docker-compose up -d --build && docker image prune -f

test:
	docker-compose run --rm app sh -c "flake8"
	docker-compose run --rm app sh -c "coverage run manage.py test"
	docker-compose run --rm app sh -c "coverage report"
	docker-compose run --rm app sh -c "coverage html"
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
	cd /d/projects/test-applications-manager-django

update_front_core:
	cd portfolio/apps/core/_dev && \
	rm -rf node_modules && \
	rm -f package-lock.json && \
	ncu && \
	ncu -u && \
	npm install && \
	npm run b && \
	rm -rf node_modules && \
	cd /d/projects/test-applications-manager-django

db-remote-backup-restore:
	docker-compose -f docker-compose.deploy.yml exec db dropdb -U $(SQL_USER) $(SQL_DATABASE)
	docker-compose -f docker-compose.deploy.yml exec db createdb -U $(SQL_USER) $(SQL_DATABASE)
	docker-compose -f docker-compose.deploy.yml exec -T db psql -U $(SQL_USER) $(SQL_DATABASE) < ../db_backup.sql

########################For Remote Host Makefile##############################
prod:
	cd test-applications-manager && \
	git pull origin && \
	docker-compose -f docker-compose.deploy.yml down && \
	docker-compose -f docker-compose.deploy.yml build && \
	docker-compose -f docker-compose.deploy.yml run --rm app sh -c "python manage.py makemigrations" && \
	docker-compose -f docker-compose.deploy.yml run --rm app sh -c "python manage.py migrate" && \
	docker-compose -f docker-compose.deploy.yml up -d && \
	cd .. && docker system prune -a --volumes -f

dev:
	cd test-applications-manager && \
	git pull origin development && \
	docker-compose -f docker-compose.deploy.yml down && \
	docker-compose -f docker-compose.deploy.yml build && \
	docker-compose -f docker-compose.deploy.yml run --rm app sh -c "python manage.py makemigrations" && \
	docker-compose -f docker-compose.deploy.yml run --rm app sh -c "python manage.py migrate" && \
	docker-compose -f docker-compose.deploy.yml up -d && \
	cd .. && docker system prune -a --volumes -f

proxy:
	cd test-applications-manager && \
	docker-compose -f docker-compose.deploy.yml down && \
	docker volume rm $$(docker volume ls -qf name=certbot-web) && \
	docker volume rm $$(docker volume ls -qf name=proxy-dhparams) && \
	docker volume rm $$(docker volume ls -qf name=certbot-certs) && \
	docker-compose -f docker-compose.deploy.yml run --rm certbot /opt/certify-init.sh && \
	docker-compose -f docker-compose.deploy.yml down && \
	docker-compose -f docker-compose.deploy.yml build && \
	docker-compose -f docker-compose.deploy.yml up -d && \
	cd .. && docker system prune -a --volumes -f

db-backup-restore:
	cd test-applications-manager && $(MAKE) db-remote-backup-restore
