#!/bin/bash

# Beat do Celery (agendador de tasks)
celery -A configuracoes beat --loglevel=info