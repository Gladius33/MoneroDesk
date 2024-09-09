#!/usr/bin/env python
import os
import sys
import unittest
from django.conf import settings
from django.apps import apps

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MoneroDesk.settings")

    try:
        from django.core.management import execute_from_command_line
        from django.apps import apps
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if 'test' in sys.argv:
        # S'assurer que les applications sont chargées avant d'exécuter les tests
        apps.populate(settings.INSTALLED_APPS)
        
        # Découverte et exécution des tests
        suite = unittest.TestLoader().discover('tests')
        runner = unittest.TextTestRunner()
        runner.run(suite)
    else:
        execute_from_command_line(sys.argv)
