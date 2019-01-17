from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from orcaserver.management.commands import runorca

from orcaserver.forms import OrcaFileForm


def get_python_file(request):
    if request.method == 'POST':
        form = OrcaFileForm(request.POST, request.FILES)
        if form.is_valid():
            module = form.cleaned_data['module']
            runorca.load_module(module)
            return HttpResponseRedirect(reverse('scenarios'))
    else:
        form = OrcaFileForm()
    return render(request, 'orcaserver/index.html', {'form': form})
