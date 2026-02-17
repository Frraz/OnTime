#!/bin/bash

# Worker + Beat juntos (apenas para desenvolvimento)
celery -A configuracoes worker --beat --loglevel=info