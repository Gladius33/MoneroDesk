from __future__ import absolute_import, unicode_literals

# Importer Celery pour qu'il soit initialisé lors du démarrage de Django
from celery import app as celery_app

__all__ = ('celery_app',)