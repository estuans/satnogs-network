#!/usr/bin/env python
import os
import dotenv
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'network.settings')

dotenv.read_dotenv(dotenv='.env')
application = get_wsgi_application()
