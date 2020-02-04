from orca import (get_step_table_names, get_step, add_injectable, clear_cache,
                  write_tables, log_start_finish, iter_step, logger)
import threading
import time
import logging
from django.utils import timezone
import ctypes

_CS_STEP = 'steps'
_CS_ITER = 'iteration'


class Singleton(object):
    """Singleton Mixin"""
    def __new__(cls, *args, **kwargs):
        key = str(hash(cls))
        if not hasattr(cls, '_instance_dict'):
            cls._instance_dict = {}
        if not hasattr(cls._instance_dict, key):
            cls._instance_dict[key] = \
                super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance_dict[key]


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
            cls._instance_dict[key] = \
                super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance_dict[key]


class OrcaManager(Singleton):
    user = ''
    start_time = ''
    running = False
    # easy way to pass arguments to run
    #_target = run
    thread = None

    def start(self, steps, user=None, logger=logging.getLogger('OrcaLog')):
        if self.thread and self.thread.isAlive():
            raise InUseError('Thread is already running')
        self.thread = AbortableThread(target=self.run)
        self.steps = steps
        self.user = user.get_username() if user else 'unknown'
        self.logger = logger
        self.start_time = timezone.now()
        self.thread.start()

    def abort(self):
        if self.thread:
            self.thread.abort()

    @property
    def is_running(self):
        return self.thread.isAlive() if self.thread else False

    def run(self, iter_vars=None, data_out=None,
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
        try:
            iter_vars = iter_vars or [None]
            max_i = len(iter_vars)
            step_names = [step.name for step in self.steps]

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

            logger = logging.getLogger('OrcaLog')
            # run the steps
            for i, var in enumerate(iter_vars, start=1):
                add_injectable('iter_var', var)

                if var is not None:
                    logger.debug(
                        'running iteration {} with iteration value {!r}'.format(
                            i, var))

                t1 = time.time()
                for j, step in enumerate(self.steps):
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

                logger.debug(
                    ('Total time to execute iteration {} '
                     'with iteration value {!r}: '
                     '{:.2f} s').format(i, var, time.time() - t1))

                # write out the results for the current iteration
                if data_out:
                    if (i - 1) % out_interval == 0 or i == max_i:
                        write_tables(data_out, out_run_tables, var,
                                     compress=compress, local=out_run_local)

                clear_cache(scope=_CS_ITER)
        except Abort:
            return
