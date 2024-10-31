from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Définir le fichier settings de Django pour Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneroDesk.settings')

# Initialisation de Celery
app = Celery('MoneroDesk')

# Charger les configurations de settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-découverte des tâches des applications installées
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    
if __name__ == '__main__':
    app.start()
