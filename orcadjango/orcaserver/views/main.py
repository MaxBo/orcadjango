from django.http import HttpResponseRedirect
from django.shortcuts import render

from orcaserver.forms import OrcaFileForm

def get_python_file(request):
    if request.method == 'POST':
        form = OrcaFileForm(request.POST, request.FILES)
        if form.is_valid():
            module = form.cleaned_data['module']
            __import__(module)
            return HttpResponseRedirect('/orca/scenarios')
    else:
        form = OrcaFileForm()
    return render(request, 'orcaserver/index.html', {'form': form})
