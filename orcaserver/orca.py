import threading
import importlib
import logging
import ctypes
import sys
import typing
from inspect import signature, _empty
import traceback

from django.utils import timezone

lock = threading.Lock()

_CS_STEP = 'steps'
_CS_ITER = 'iteration'

logger = logging.getLogger('scenario')

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
        #  if the modules are not reloaded yet
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


class ModuleSingleton(object):
    _instance_dict = {}

    def __new__(cls, *args, **kwargs):
        key = args[0]
        if not key in cls._instance_dict:
            with lock:
                cls._instance_dict[key] = super().__new__(cls)
        return cls._instance_dict[key]


class OrcaManager(ModuleSingleton):
    ''''''
    module = None
    instances = {}
    meta = {}
    __generic_instance = None

    def __init__(self, module_path: str):
        self.module = module_path
        if not self.__generic_instance:
            self.__generic_instance = self.create_instance()

    def get_calculated_value(self, injectable, *args):
        funcwrapper = self.__generic_instance.orca.get_raw_injectable(injectable)
        sig = signature(funcwrapper._func)
        parameters = list(sig.parameters.keys())
        # calculate value if injectable function has parameters (meaning
        # parent injectables)
        if not parameters:
            return None
        return funcwrapper._func(*args)

    def get_step_names(self):
        return self.__generic_instance.orca.list_steps()

    def get_injectable_names(self):
        return self.__generic_instance.orca.list_injectables()

    def _get_orca_meta(self):
        return getattr(self.__generic_instance.orca, 'meta', {})

    def get_step_meta(self, step: str):
        meta = self._get_orca_meta()
        step_meta = meta.get(step, {})
        required = step_meta.get('required')
        if not isinstance(required, list):
            required = [required]
        required = [r.__name__ if callable(r) else str(r) for r in required]
        wrapper = self.__generic_instance.orca.get_step(step)
        sig = signature(wrapper._func)
        inj_parameters = sig.parameters
        inj_available = self.__generic_instance.orca.list_injectables()
        injectables = [pinj for pinj in inj_parameters if pinj in inj_available]
        return {
            'name': step,
            'title': step_meta.get('title', ''),
            'group': step_meta.get('group', '-'),
            'order': step_meta.get('order', 1),
            'docstring': step_meta.get('description') or wrapper._func.__doc__ or '',
            'injectables': injectables,
            'required': required,
        }

    def get_injectable_meta(self, injectable: str):
        orca_injectables = self.__generic_instance.orca.list_injectables()
        orca_meta = self._get_orca_meta()
        # defaults (required by serializer)
        desc = {
            'order': 10000000,
            'group': '',
            'title': '',
            'unique': False
        }
        _meta = orca_meta.get(injectable, {})
        if (injectable not in orca_injectables or injectable.startswith('iter_')
            or _meta.get('hidden')):
            return {}
        if _meta.get('refresh') == 'always':
            value = self.__generic_instance.orca.get_injectable(injectable)
        else:
            value = self.__generic_instance.orca._injectable_backup.get(injectable)
        datatype_class = type(value)
        datatype = datatype_class.__name__
        desc['datatype'] = datatype
        # check if the original type is overwritable
        funcwrapper = self.__generic_instance.orca.get_raw_injectable(injectable)
        sig = signature(funcwrapper._func)
        if isinstance(funcwrapper, self.__generic_instance.orca._InjectableFuncWrapper):
            desc['docstring'] = _meta.get('description') or funcwrapper._func.__doc__ or ''
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
                c_meta = self.__generic_instance.orca.meta.get(choices.__name__)
                if c_meta and c_meta.get('refresh') == 'always':
                    choices = self.__generic_instance.orca.get_injectable(choices.__name__)
                else:
                    choices = self.__generic_instance.orca._injectable_backup.get(choices.__name__)
                desc['choices'] = choices
            desc['parameters'] = list(sig.parameters.keys())

        desc['data_class'] = (f'{datatype_class.__module__}.'
                              f'{datatype_class.__name__}')
        desc['default'] = self.__generic_instance.orca.get_injectable(injectable)
        return desc

    def get_instance(self, instance_id: int, create: bool = True):
        with lock:
            instance = self.instances.get(instance_id)
            if not instance and create:
                return self.create_instance(instance_id)
            return instance

    def create_instance(self, instance_id: int = None):
        instance = OrcaWrapper(self.module)
        if (instance_id):
            self.instances[instance_id] = instance
        return instance

    def reset(self):
        with lock:
            if 'orca' in sys.modules:
                del(sys.modules['orca'])
            for iid in list(self.instances.keys()):
                self.instances[iid].remove()
                del(self.instances[iid])

    def is_running(self, instance_id: int = None):
        orca_wrapper = self.instances.get(instance_id)
        return orca_wrapper.is_running() if orca_wrapper else False


class OrcaWrapper():

    def __init__(self, module: str):
        self.thread = None
        self.module = module
        self.orca = self.__create_instance()

    def __create_instance(self) -> 'module':
        spec = importlib.util.find_spec('orca.orca')
        orca = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(orca)
        # append a logger
        orca.logger = logging.getLogger(str(id(orca)))
        orca.logger.setLevel(logging.DEBUG)
        sys.modules['orca'] = orca
        from orcadjango import decorators
        importlib.reload(decorators)
        load_module(self.module, orca=orca)
        del(spec)
        if 'orca' in sys.modules:
            del(sys.modules['orca'])
        return orca

    def add_log_handler(self, handler: logging.StreamHandler):
        self.orca.logger.addHandler(handler)

    def clear_log_handlers(self):
        self.orca.logger.handlers.clear()

    def set_value(self, injectable: str, value):
        self.orca.add_injectable(injectable, value)

    def start(self, steps, on_success=None, on_error=None):
        if self.is_running():
            raise InUseError('Thread is already running')
        self.thread = AbortableThread(
            target=self.__run, args=(steps, ))
        self.thread.on_success = on_success
        self.thread.on_error = on_error
        message = f'Starting run...'
        self.orca.logger.info(message)
        self.thread.start()

    def abort(self):
        if self.is_running():
            self.orca.logger.error('aborting...')
            self.thread.abort()

    def is_running(self):
        return self.thread.is_alive() if self.thread else False

    def remove(self):
        if self.is_running():
            raise Exception(
                'The orca instances can not be reset at the moment.'
                ' A thread is still running.')
        if self.thread:
            del(self.thread)
        self.clear_log_handlers()

    def __run(self, steps, iter_vars=None, data_out=None,
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
        logger = self.orca.logger
        try:
            iter_vars = iter_vars or [None]
            max_i = len(iter_vars)
            step_names = [step.name for step in steps]

            # get the tables to write
            if out_base_tables is None or out_run_tables is None:
                step_tables = self.orca.get_step_table_names(step_names)

                if out_base_tables is None:
                    out_base_tables = step_tables

                if out_run_tables is None:
                    out_run_tables = step_tables

            # write the base data (inputs)
            if data_out:
                self.orca.add_injectable('iter_var', iter_vars[0])
                self.orca.write_tables(
                    data_out, out_base_tables, 'base', compress=compress,
                    local=out_base_local)
            logger.info("Run started",
                        extra={'status': {'started': True}})

            # run the steps
            for i, var in enumerate(iter_vars, start=1):
                self.orca.add_injectable('iter_var', var)

                if var is not None:
                    logger.debug(
                        'running iteration {} with iteration value {!r}'.format(
                            i, var))

                for j, step in enumerate(steps):
                    step_name = step.name
                    self.orca.add_injectable(
                        'iter_step', self.orca.iter_step(j, step_name))
                    logger.info(f"Running step '{step_name}'",
                                extra={'status': {
                                    'step': step_name,
                                    'started': True
                                }})
                    step_func = self.orca.get_step(step_name)
                    step.started = timezone.now()
                    step.save()
                    try:
                        step_func()
                        step.success = True
                    except Exception as e:
                        step.success = False
                        step.finished = timezone.now()
                        step.save()
                        logger.debug(traceback.format_exc())
                        logger.error(
                            f'{e.__class__.__module__}.'
                            f'{e.__class__.__name__} - {str(e)}')
                        logger.error(f'{step_name} failed',
                                     extra={'status': {
                                         'step': step_name,
                                         'finished': True,
                                         'success': False
                                     }})
                        logger.error('orca run aborted',
                                     extra={'status': {
                                        'finished': True,
                                        'success': False
                                    }})
                        if self.thread.on_error:
                            self.thread.on_error()
                        return
                    step.finished = timezone.now()
                    step.active = False
                    logger.info(f'{step_name} finished',
                                extra={'status': {
                                    'step': step_name,
                                    'finished': True,
                                    'success': True
                                }})
                    step.save()

                    self.orca.clear_cache(scope=_CS_STEP)

                # write the results of the current iteration
                if data_out:
                    if (i - 1) % out_interval == 0 or i == max_i:
                        self.orca.write_tables(
                            data_out, out_run_tables, var,
                            compress=compress, local=out_run_local)

                self.orca.clear_cache(scope=_CS_ITER)
            logger.info('orca run finished', extra={
                'status': {'finished': True, 'success': True}})
            if self.thread.on_success:
                self.thread.on_success()
        except Abort:
            logger.error('orca run aborted', extra={
                'status': {'finished': True, 'success': False}})
            if self.thread.on_error:
                self.thread.on_error()
        finally:
            self.orca.clear_cache()