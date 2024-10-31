from __future__ import absolute_import, unicode_literals

# Importer Celery pour qu'il soit initialisé lors du démarrage de Django
from .celery_app import app


__all__ = ('app',)