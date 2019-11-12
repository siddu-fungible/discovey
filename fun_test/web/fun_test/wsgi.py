"""
WSGI config for web project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

'''
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.fun_test.settings")
os.environ["PERFORMACE_SERVER"] = "1"

application = get_wsgi_application()


'''
from django.core.handlers.wsgi import WSGIHandler
import django
import os
#os.environ["PERFORMANCE_SERVER"] = "1"
os.environ["DEVELOPMENT_MODE"] = "1"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.fun_test.settings")
django.setup()
class WSGIEnvironment(WSGIHandler):

    def __call__(self, environ, start_response):
        #os.environ["PERFORMANCE_SERVER"] = "1"
        #os.environ["PERFORMANCE_SERVER"] = "1"
        os.environ["DEVELOPMENT_MODE"] = "1"


        return super(WSGIEnvironment, self).__call__(environ, start_response)
django.setup(set_prefix=False)
application = WSGIEnvironment()
