from urllib import response

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST, require_GET, require_http_methods

# import messages
from django.contrib import messages

import logging

# make logging level debug and create a logger called log
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def home(request):
    template_name = "django_nominopolitan/index.html"
    context = {'header_title': "Home"}
    if request.htmx:
        return render(request, f"{template_name}#content", context)
    return render(request, template_name, context)
    