from collections import OrderedDict
from django.views.generic import TemplateView
from django.views.generic.edit import BaseFormView
from django.shortcuts import render, HttpResponseRedirect
import orca
from orcaserver.views import ScenarioMixin
from orcaserver.models import Step, Injectable, Scenario
from django.urls import reverse
from threading import Thread
import time
import contextlib
import logging
from django.utils import timezone
from django.http import JsonResponse, HttpResponseNotFound

def apply_injectables(scenario):
    names = orca.list_injectables()
    injectables = Injectable.objects.filter(name__in=names, scenario=scenario)
    for inj in injectables:
        orca.add_injectable(inj.name, inj.value)


class StepsView(ScenarioMixin, TemplateView):
    template_name = 'orcaserver/steps.html'

    def get_context_data(self, **kwargs):
        steps_available = OrderedDict(((name, orca.get_step(name))
                                       for name in orca.list_steps()))
        scenario = self.get_scenario()
        steps_scenario = Step.objects.filter(
            scenario=scenario).order_by('order')
        kwargs = super().get_context_data(**kwargs)
        kwargs['steps_available'] = steps_available
        kwargs['steps_scenario'] = steps_scenario
        return kwargs

    @staticmethod
    def list(request):
        scenario_id = request.session.get('scenario')
        if scenario_id is None:
            return HttpResponseNotFound('scenario not found')
        scenario = Scenario.objects.get(id=scenario_id)
        steps_scenario = Step.objects.filter(
            scenario=scenario).order_by('order')
        steps_json = []
        for step in steps_scenario:
            started = step.started
            finished = step.finished
            if started:
                started = started.strftime("%a %b %d %H:%M:%S %Z %Y")
            if finished:
                finished = finished.strftime("%a %b %d %H:%M:%S %Z %Y")
            steps_json.append({
                'id': step.id,
                'name': step.name,
                'started': started,
                'finished': finished,
                'success': step.success,
            })
        return JsonResponse(steps_json, safe=False)

    def post(self, request, *args, **kwargs):
        scenario = self.get_scenario()
        if request.POST.get('add'):
            steps = request.POST.get('add_steps', '').split(',')
            for step in steps:
                if not step:
                    continue
                Step.objects.create(scenario=scenario,
                                    name=step, order=10000)
        elif request.POST.get('remove'):
            steps = request.POST.get('selected_steps', '').split(',')
            for step_id in steps:
                if not step_id:
                    continue
                step = Step.objects.get(id=step_id)
                step.delete()
        elif request.POST.get('run'):
            selected = request.POST.get('selected_steps')
            if selected:
                steps = Step.objects.filter(
                    id__in=selected.rstrip(',').split(','))
            else:
                steps = Step.objects.filter(scenario=self.get_scenario())
            steps = steps.order_by('order')
            for step in steps:
                step.started = None
                step.finished = None
                step.success = False
                step.save()
            apply_injectables(self.get_scenario())
            thread = Thread(target=run, args=(steps, ))
            thread.start()
        return HttpResponseRedirect(request.path_info)

from orca import (get_step_table_names, get_step, add_injectable, clear_cache,
                  write_tables, log_start_finish, iter_step, logger)
_CS_STEP = 'steps'
_CS_ITER = 'iteration'

def run(steps, iter_vars=None, data_out=None, out_interval=1,
        out_base_tables=None, out_run_tables=None, compress=False,
        out_base_local=True, out_run_local=True):
    """
    Run steps in series, optionally repeatedly over some sequence.
    The current iteration variable is set as a global injectable
    called ``iter_var``.

    Parameters
    ----------
    steps : list of Step
    iter_vars : iterable, optional
        The values of `iter_vars` will be made available as an injectable
        called ``iter_var`` when repeatedly running `steps`.
    data_out : str, optional
        An optional filename to which all tables injected into any step
        in `steps` will be saved every `out_interval` iterations.
        File will be a pandas HDF data store.
    out_interval : int, optional
        Iteration interval on which to save data to `data_out`. For example,
        2 will save out every 2 iterations, 5 every 5 iterations.
        Default is every iteration.
        The results of the first and last iterations are always included.
        The input (base) tables are also included and prefixed with `base/`,
        these represent the state of the system before any steps have been
        executed.
        The interval is defined relative to the first iteration. For example,
        a run begining in 2015 with an out_interval of 2, will write out
        results for 2015, 2017, etc.
    out_base_tables: list of str, optional, default None
        List of base tables to write. If not provided, tables injected
        into 'steps' will be written.
    out_run_tables: list of str, optional, default None
        List of run tables to write. If not provided, tables injected
        into 'steps' will be written.
    compress: boolean, optional, default False
        Whether to compress output file using standard HDF5 zlib compression.
        Compression yields much smaller files using slightly more CPU.
    out_base_local: boolean, optional, default True
        For tables in out_base_tables, whether to store only local columns (True)
        or both, local and computed columns (False).
    out_run_local: boolean, optional, default True
        For tables in out_run_tables, whether to store only local columns (True)
        or both, local and computed columns (False).
    """
    iter_vars = iter_vars or [None]
    max_i = len(iter_vars)
    step_names = [step.name for step in steps]

    # get the tables to write out
    if out_base_tables is None or out_run_tables is None:
        step_tables = get_step_table_names(step_names)

        if out_base_tables is None:
            out_base_tables = step_tables

        if out_run_tables is None:
            out_run_tables = step_tables

    # write out the base (inputs)
    if data_out:
        add_injectable('iter_var', iter_vars[0])
        write_tables(data_out, out_base_tables, 'base', compress=compress,
                     local=out_base_local)

    # run the steps
    for i, var in enumerate(iter_vars, start=1):
        add_injectable('iter_var', var)

        if var is not None:
            print('Running iteration {} with iteration value {!r}'.format(
                i, var))
            logger.debug(
                'running iteration {} with iteration value {!r}'.format(
                    i, var))

        t1 = time.time()
        for j, step in enumerate(steps):
            step_name = step.name
            add_injectable('iter_step', iter_step(j, step_name))
            print('Running step {!r}'.format(step_name))
            with log_start_finish(
                    'run step {!r}'.format(step_name), logger,
                    logging.INFO):
                step_func = get_step(step_name)
                t2 = time.time()
                step.started = timezone.now()
                step.save()
                try:
                    step_func()
                    step.success = True
                except Exception as e:
                    step.success = False
                    raise e
                end = time.time() - t2
                print("Time to execute step '{}': {:.2f} s".format(
                      step_name, end))
                step.finished = timezone.now()
                step.save()


            clear_cache(scope=_CS_STEP)

        print(
            ('Total time to execute iteration {} '
             'with iteration value {!r}: '
             '{:.2f} s').format(i, var, time.time() - t1))

        # write out the results for the current iteration
        if data_out:
            if (i - 1) % out_interval == 0 or i == max_i:
                write_tables(data_out, out_run_tables, var, compress=compress, local=out_run_local)

        clear_cache(scope=_CS_ITER)
