#!/bin/bash

# Worker do Celery
celery -A configuracoes worker --loglevel=info --concurrency=4