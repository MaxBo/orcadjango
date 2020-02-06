import orca
from typing import List
from time import sleep
from orcadjango.decorators import group
import logging
logger = logging.getLogger('OrcaLog')


@group(groupname='strings', order=1)
@orca.injectable()
def inj1() -> str:
    return 'INJ 1'


@group(groupname='strings', order=2)
@orca.injectable()
def inj2():
    return 'INJ 2'


@group(groupname='ints', order=2)
@orca.injectable()
def inj_int() -> int:
    """The answer is 42"""
    return 42


@group(groupname='ints', order=1)
@orca.injectable()
def inj_list() -> List[int]:
    return [2, 3, 66]


@group(groupname='das dict')
@orca.injectable()
def inj_dict():
    return dict(a=1, b=-1)


from contextlib import ContextDecorator


class mycontext(ContextDecorator):
    def __enter__(self):
        print('Starting')
        return self

    def __exit__(self, *exc):
        print('Finishing')
        return False


@group(groupname='Hallo', order=2)
@orca.step()
def step2(inj1, inj2):
    """another dummy step"""
    with mycontext():
        print('start')
        for i in range(10):
            sleep(1)
            print(i)


@group(groupname='Hallo', order=1)
@orca.step()
def step1(inj_list):
    """dummy step"""
    sleep(5)


@group(groupname='Huhu')
@orca.step()
def step_dict(inj_dict):
    """another dummy step with dict"""
    for k, v in inj_dict.items():
        logger.disabled = False
        logger.info(f'{k}: {v}')
        sleep(1)
