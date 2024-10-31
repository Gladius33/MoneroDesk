from __future__ import absolute_import, unicode_literals

# Importer Celery pour qu'il soit initialisé lors du démarrage de Django
from MoneroDesk.celery_app import app as celery_app


__all__ = ('celery_app',)