import os
from django.shortcuts import render
from django.template import loader
import orca

# Create your views here.
import orca

@orca.injectable()
def inj1():
    return 'INJ 1'

@orca.injectable()
def inj2():
    return 'INJ 2'


from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the index.")

def injectable(request, name):
    value = orca.get_injectable(name)
    return HttpResponse(f"Injectable {name} is {value}.")

def injectables(request):
    template = loader.get_template('orcaserver/injectables.html')
    context = {
        'injectable_list': orca.list_injectables(),
    }
    return HttpResponse(template.render(context, request))