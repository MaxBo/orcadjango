import time
import ast
import logging
import json
from collections import OrderedDict
from django.views.generic import TemplateView
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone
from django.http import JsonResponse, HttpResponseNotFound
import orca
from orca import (get_step_table_names, get_step, add_injectable, clear_cache,
                  write_tables, log_start_finish, iter_step, logger)

from orcaserver.views import ScenarioMixin
from orcaserver.models import Step, Injectable, Scenario
from django.core.exceptions import ObjectDoesNotExist
from threading import Thread
from django.urls import reverse
import json


def apply_injectables(scenario):
    names = orca.list_injectables()
    injectables = Injectable.objects.filter(name__in=names, scenario=scenario)
    for inj in injectables:
        #  skip injectables which cannot be changed
        if not (inj.changed or inj.can_be_changed):
            continue
        #  get original type of injectable value (if not available, use string)
        original_type = type(orca._injectable_backup.get(inj.name, str))
        # compare to evaluation or value
        if inj.value is None:
            func = orca._injectable_function.get(inj.name)
            if func:
                converted_value = func()
            else:
                converted_value = orca.get_injectable(inj.name)
        elif issubclass(original_type, str):
            converted_value = inj.value
        else:
            try:
                converted_value = ast.literal_eval(inj.value)
                if not isinstance(converted_value, original_type):
                    #  try to cast the value using the original type
                    converted_value = original_type(inj.value)
            except (SyntaxError, ValueError) as e:

                # if casting does not work, raise warning
                # and use original value
                msg = (f'Injectable `{inj.name}` with value `{inj.value}` '
                       f'could not be casted to type `{original_type}`.'
                       f'Injectable Value was not overwritten.'
                       f'Error message: {repr(e)}')
                logger.warning(msg)
                continue
        orca.add_injectable(inj.name, converted_value)


class StepsView(ScenarioMixin, TemplateView):
    template_name = 'orcaserver/steps.html'

    @property
    def id(self):
        return self.kwargs.get('id')

    def get_context_data(self, **kwargs):
        scenario = self.get_scenario()
        steps = OrderedDict(((name, orca.get_step(name)._func.__doc__)
                             for name in orca.list_steps()))
        steps_available = steps if scenario else {}
        steps_scenario = Step.objects.filter(
            scenario=scenario).order_by('order')
        kwargs = super().get_context_data(**kwargs)
        kwargs['steps_available'] = steps_available
        kwargs['steps_scenario'] = steps_scenario
        return kwargs

    @staticmethod
    def list(request):
        if request.method == 'POST':
            body = json.loads(request.body)
            for item in body:
                step = Step.objects.get(id=item['id'])
                step.order = item['order']
                step.save()
        scenario_id = request.session.get('scenario')
        if scenario_id is None:
            return HttpResponseNotFound('scenario not found')
        scenario = Scenario.objects.get(id=scenario_id)
        steps_scenario = Step.objects.filter(
            scenario=scenario).order_by('order')
        steps_json = []
        injectables_available = orca.list_injectables()
        for step in steps_scenario:
            func = orca.get_step(step.name)
            inj_names = func._func.__code__.co_varnames
            injectables = []
            for name in inj_names:
                if name not in injectables_available:
                    continue
                inj = Injectable.objects.get(name=name, scenario=scenario)
                injectables.append({
                    'id': inj.id,
                    'name': name,
                    'value': inj.value,
                    'url': f"{reverse('injectables')}{name}",
                })
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
                'order': step.order,
                'is_active': step.active,
                'injectables': injectables
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
                    id__in=selected.rstrip(',').split(',')).\
                    filter(active=True)
            else:
                steps = Step.objects.filter(scenario=self.get_scenario()).\
                    filter(active=True)
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

    # to do for updating is_active
    @staticmethod
    def detail(request, *args, **kwargs):
        step_id = kwargs.get('id')
        if request.method == 'PATCH':
            try:
                step = Step.objects.get(id=step_id)
            except ObjectDoesNotExist:
                return JsonResponse({}, safe=False)
            body = json.loads(request.body)
            is_active = body.get('is_active')
            step.active = is_active
            step.save()
            return JsonResponse({}, safe=False)

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
                write_tables(data_out, out_run_tables, var,
                             compress=compress, local=out_run_local)

        clear_cache(scope=_CS_ITER)
