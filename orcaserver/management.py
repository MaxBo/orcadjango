import threading
import importlib
import logging
import ctypes
import sys
import typing
from inspect import signature, _empty

from django.utils import timezone

lock = threading.Lock()

_CS_STEP = 'steps'
_CS_ITER = 'iteration'

def load_module(module_name, orca=None, module_set=None):
    if not orca:
        import orca
    if module_set is None:
        orca._python_module = module_name
        orca.clear_all()
        orca._injectable_backup = {}
        orca._injectable_function = {}
        module_set = {module_name}

    spec = importlib.util.find_spec(module_name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for inj in orca.list_injectables():
        orca._injectable_function[inj] = orca._INJECTABLES[inj]
        try:
            orca._injectable_backup[inj] = orca.get_injectable(inj)
        except KeyError as e:
            orca._injectable_backup[inj] = repr(e)

    # reload the parent modules
    parent_modules = getattr(module, '__parent_modules__', [])
    for module_name in parent_modules:
        #  if the are not reloaded yet
        if not module_name in module_set:
            load_module(module_name, orca=orca, module_set=module_set)
            module_set.add(module_name)
    return module


class InUseError(Exception):
    ''''''


class Abort(Exception):
    ''''''


class AbortableThread(threading.Thread):

    def get_id(self):
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for _id, thread in threading._active.items():
            if thread is self:
                self._thread_id = _id
                return _id

    def abort(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), ctypes.py_object(Abort))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(thread_id), 0)
            print('Exception raise failure')


class Singleton(object):
    """Singleton Mixin"""
    _instance_dict = {}

    def __new__(cls, *args, **kwargs):
        key = str(hash(cls))
        if not key in cls._instance_dict:
            with lock:
                cls._instance_dict[key] = \
                    super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance_dict[key]


class OrcaManager(Singleton):
    ''''''
    instances = {}
    threads = {}
    meta = {}
    default_module = None
    _mod_instances = {}

    #@property
    #def descriptors(self):
        #if self._descriptors is not None:
            #return self._descriptors
        #parse_injectables


    #def get_orca(self, scenario=None):
        #scenario = scenario or self.get_scenario()
        #if not scenario:
            #return
        #module = self.get_module()
        #orca = manager.get(scenario.id, module=module, create=False)
        #if not orca:
            #orca = manager.create(scenario.id, module=module)
            #handler = ScenarioHandler(scenario, persist=True)
            #level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
            #handler.setLevel(level)
            #manager.add_log_handler(scenario.id, handler)
            #apply_injectables(orca, scenario)
        #return orca

    def get_calculated_value(self, injectable, module, *args):
        orca = self._mod_instances.get(module)
        if not orca:
            orca = self._mod_instances[module] = self.create(module=module)

        funcwrapper = orca.get_raw_injectable(injectable)
        sig = signature(funcwrapper._func)
        parameters = list(sig.parameters.keys())
        # calculate value if injectable function has parameters (meaning
        # parent injectables)
        if not parameters:
            return None
        return funcwrapper._func(*args)

    def get_meta(self, injectable: str, module: str):
        orca = self._mod_instances.get(module)
        if not orca:
            orca = self._mod_instances[module] = self.create(module=module)
        orca_injectables = orca.list_injectables()
        orca_meta = getattr(orca, 'meta', {})
        # defaults (required by serializer)
        desc = {
            'order': 10000000,
            'group': '',
        }
        _meta = orca_meta.get(injectable, {})
        if (injectable not in orca_injectables or injectable.startswith('iter_')
            or _meta.get('hidden')):
            return {}
        if _meta.get('refresh') == 'always':
            value = orca.get_injectable(injectable)
        else:
            value = orca._injectable_backup.get(injectable)
        datatype_class = type(value)
        datatype = datatype_class.__name__
        desc['datatype'] = datatype
        # check if the original type is overwritable
        funcwrapper = orca.get_raw_injectable(injectable)
        sig = signature(funcwrapper._func)
        if isinstance(funcwrapper, orca._InjectableFuncWrapper):
            desc['docstring'] = funcwrapper._func.__doc__ or ''
            # datatype from annotations
            returntype = sig.return_annotation
            has_returntype = True
            if isinstance(returntype, type) and issubclass(returntype, _empty):
                has_returntype = False
            if has_returntype:
                if isinstance(returntype, typing._GenericAlias):
                    datatype_class = returntype.__origin__
                    desc['datatype'] = str(returntype)
                else:
                    datatype_class = returntype
                    desc['datatype'] = returntype.__name__
            desc['module'] = funcwrapper._func.__module__
            desc.update(_meta)
            choices = desc.get('choices')
            # choices are derived from another injectable
            if callable(choices):
                c_meta = orca.meta.get(choices.__name__)
                if c_meta and c_meta.get('refresh') == 'always':
                    choices = orca.get_injectable(choices.__name__)
                else:
                    choices = orca._injectable_backup.get(choices.__name__)
                desc['choices'] = choices
            desc['parameters'] = list(sig.parameters.keys())

        desc['data_class'] = (f'{datatype_class.__module__}.'
                              f'{datatype_class.__name__}')
        return desc

    def set_default_module(self, module: str):
        self.reset()
        self.default_module = module

    def get(self, instance_id: int, create: bool = True, module: str = None):
        with lock:
            instance = self.instances.get(instance_id)
            if instance and module and instance._python_module != module:
                raise Exception('The requested orca instance was built with '
                                f'the module {instance._python_module} instead '
                                f'of the requested module {module}')
            if not instance and create:
                return self.create(instance_id, module=module)
            return instance

    def remove(self, instance_id: int):
        if instance_id not in self.instances:
            return
        if self.is_running(instance_id):
            raise Exception(
                'The orca instances can not be reset at the moment.'
                ' A thread is still running.')
        self.clear_log_handlers(instance_id)
        del(self.instances[instance_id])
        if instance_id in self.threads:
            del(self.threads[instance_id])

    def create(self, instance_id: int = None, module: str = None):
        instance = self._create_instance(module or self.default_module)
        if (instance_id):
            self.instances[instance_id] = instance
        return instance

    def add_log_handler(self, instance_id: int, handler: logging.StreamHandler):
        instance = self.instances[instance_id]
        instance.logger.addHandler(handler)

    def clear_log_handlers(self, instance_id: int):
        instance = self.instances.get(instance_id)
        if not instance:
            return
        instance.logger.handlers.clear()

    def _create_instance(self, module_name) -> 'module':
        spec = importlib.util.find_spec('orca.orca')
        orca = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(orca)
        # append a logger
        orca.logger = logging.getLogger(str(id(orca)))
        orca.logger.setLevel(logging.DEBUG)
        sys.modules['orca'] = orca
        from orcadjango import decorators
        importlib.reload(decorators)
        load_module(module_name, orca=orca)
        del(spec)
        del(sys.modules['orca'])
        return orca

    def reset(self):
        with lock:
            if 'orca' in sys.modules:
                del(sys.modules['orca'])
            for iid in list(self.instances.keys()):
                self.remove(iid)

    def start(self, instance_id: int, steps, on_success=None,
              on_error=None):
        thread = self.threads.get(instance_id)
        if thread and thread.isAlive():
            raise InUseError('Thread is already running')
        thread = self.threads[instance_id] = AbortableThread(
            target=self.run, args=(instance_id, steps))
        thread.on_success = on_success
        thread.on_error = on_error
        thread.start()

    def abort(self, instance_id):
        thread = self.threads.get(instance_id)
        if thread and thread.isAlive():
            orca = self.get(instance_id)
            orca.logger.error('aborting...')
            thread.abort()

    def is_running(self, instance_id: int):
        thread = self.threads.get(instance_id)
        return thread.isAlive() if thread else False

    def add_meta(self, instance_id, **kwargs):
        if instance_id not in self.meta:
            self.meta[instance_id] = {}
        for k, v in kwargs.items():
            self.meta[instance_id][k] = v

    def run(self, instance_id: int, steps, iter_vars=None, data_out=None,
            out_interval=1, out_base_tables=None, out_run_tables=None,
            compress=False, out_base_local=True, out_run_local=True):
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
            a run begining in 2015 with an out_interval of 2, will write
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
        orca = self.get(instance_id)
        logger = orca.logger
        thread = self.threads[instance_id]
        try:
            iter_vars = iter_vars or [None]
            max_i = len(iter_vars)
            step_names = [step.name for step in steps]

            # get the tables to write
            if out_base_tables is None or out_run_tables is None:
                step_tables = orca.get_step_table_names(step_names)

                if out_base_tables is None:
                    out_base_tables = step_tables

                if out_run_tables is None:
                    out_run_tables = step_tables

            # write the base data (inputs)
            if data_out:
                orca.add_injectable('iter_var', iter_vars[0])
                orca.write_tables(
                    data_out, out_base_tables, 'base', compress=compress,
                    local=out_base_local)

            # run the steps
            for i, var in enumerate(iter_vars, start=1):
                orca.add_injectable('iter_var', var)

                if var is not None:
                    logger.debug(
                        'running iteration {} with iteration value {!r}'.format(
                            i, var))

                for j, step in enumerate(steps):
                    step_name = step.name
                    orca.add_injectable(
                        'iter_step', orca.iter_step(j, step_name))
                    logger.info(f"Running step '{step_name}'")
                    step_func = orca.get_step(step_name)
                    step.started = timezone.now()
                    step.save()
                    try:
                        step_func()
                        step.success = True
                    except Exception as e:
                        step.success = False
                        step.finished = timezone.now()
                        step.save()
                        logger.error(
                            f'{e.__class__.__module__}.'
                            f'{e.__class__.__name__} - {str(e)}')
                        logger.error('Aborting run')
                        if thread.on_error:
                            thread.on_error()
                        return
                    step.finished = timezone.now()
                    step.active = False
                    step.save()

                    orca.clear_cache(scope=_CS_STEP)

                # write the results of the current iteration
                if data_out:
                    if (i - 1) % out_interval == 0 or i == max_i:
                        orca.write_tables(
                            data_out, out_run_tables, var,
                            compress=compress, local=out_run_local)

                orca.clear_cache(scope=_CS_ITER)
            logger.info('orca run finished')
            if thread.on_success:
                thread.on_success()
        except Abort:
            logger.error('orca run aborted')
            if thread.on_error:
                thread.on_error()
        finally:
            orca.clear_cache()