import threading
import importlib
import time
import logging
from django.utils import timezone
import ctypes
import sys

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
    module = importlib.import_module(module_name)
    importlib.reload(module)
    for inj in orca.list_injectables():
        orca._injectable_function[inj] = orca._INJECTABLES[inj]
        try:
            orca._injectable_backup[inj] = orca.get_injectable(inj)
        except Exception as e:
            orca._injectable_backup[inj] = repr(e)

    # reload the parent modules
    parent_modules = getattr(module, '__parent_modules__', [])
    for module_name in parent_modules:
        #  if the are not reloaded yet
        if not module_name in module_set:
            load_module(module_name, module_set)
            module_set.add(module_name)


class InUseError(Exception):
    ''''''


class Abort(Exception):
    ''''''


class AbortableThread(threading.Thread):

    def get_id(self):
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def abort(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            thread_id, ctypes.py_object(Abort))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
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
    python_module = None

    def set_module(self, module: str):
        self.reset()
        self.python_module = module

    def get(self, instance_id: int):
        with lock:
            if instance_id not in self.instances:
                self.instances[instance_id] = self.create_instance()
            return self.instances[instance_id]

    def create_instance(self) -> 'module':
        spec = importlib.util.find_spec('orca.orca')
        orca = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(orca)
        sys.modules['orca'] = orca
        load_module(self.python_module, orca=orca)
        del(spec)
        del(sys.modules['orca'])
        return orca

    def reset(self):
        with lock:
            for iid, instance in self.instances.items():
                thread = self.threads.get(iid)
                if thread and thread.isAlive():
                    raise Exception(
                        'The orca instances can not be reset at the moment.'
                        ' A thread is still running.')
                del(self.instances[iid])
                if thread:
                    del(self.threads[iid])

    def start(self, instance_id: int, steps, user=None):
        thread = self.threads.get(instance_id)
        if thread and thread.isAlive():
            raise InUseError('Thread is already running')
        thread = self.threads[instance_id] = AbortableThread(
            target=self.run, args=(instance_id, ))
        self.steps = steps
        self.user = user.get_username() if user else 'unknown'
        self.start_time = timezone.now()
        thread.start()

    def abort(self, instance_id):
        thread = self.threads.get(instance_id)
        if thread:
            thread.abort()

    def is_running(self, instance_id: int):
        thread = self.threads.get(instance_id)
        return thread.isAlive() if thread else False

    def run(self, instance_id: int, iter_vars=None, data_out=None,
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
        orca = self.get(instance_id)
        logger = logging.getLogger('OrcaLog')
        try:
            iter_vars = iter_vars or [None]
            max_i = len(iter_vars)
            step_names = [step.name for step in self.steps]

            # get the tables to write out
            if out_base_tables is None or out_run_tables is None:
                step_tables = orca.get_step_table_names(step_names)

                if out_base_tables is None:
                    out_base_tables = step_tables

                if out_run_tables is None:
                    out_run_tables = step_tables

            # write out the base (inputs)
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

                t1 = time.time()
                for j, step in enumerate(self.steps):
                    step_name = step.name
                    orca.add_injectable(
                        'iter_step', orca.iter_step(j, step_name))
                    print('Running step {!r}'.format(step_name))
                    with orca.log_start_finish(
                            'run step {!r}'.format(step_name), logger,
                            logging.INFO):
                        step_func = orca.get_step(step_name)
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

                    orca.clear_cache(scope=_CS_STEP)

                logger.debug(
                    ('Total time to execute iteration {} '
                     'with iteration value {!r}: '
                     '{:.2f} s').format(i, var, time.time() - t1))

                # write out the results for the current iteration
                if data_out:
                    if (i - 1) % out_interval == 0 or i == max_i:
                        orca.write_tables(
                            data_out, out_run_tables, var,
                            compress=compress, local=out_run_local)

                orca.clear_cache(scope=_CS_ITER)
            logger.info('orca run finished')
        except Abort:
            logger.info('orca run aborted')