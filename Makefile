.PHONY: instalar migrar servidor celery shell teste limpar

instalar:
	pip install -r requirements_dev.txt

migrar:
	python manage.py makemigrations
	python manage.py migrate

servidor:
	python manage.py runserver

celery:
	celery -A celery_app worker -l info

celery-beat:
	celery -A celery_app beat -l info

shell:
	python manage.py shell_plus

teste:
	pytest --tb=short -v

cobertura:
	coverage run -m pytest
	coverage report -m

limpar:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

celery:
	celery -A configuracoes worker --loglevel=info

beat:
	celery -A configuracoes beat --loglevel=info

celery-dev:
	celery -A configuracoes worker --beat --loglevel=info

flower:
	celery -A configuracoes flower --port=5555