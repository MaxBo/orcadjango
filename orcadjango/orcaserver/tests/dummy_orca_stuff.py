import orca
from typing import List
from time import sleep
from orcadjango.decorators import group
import logging
logger = logging.getLogger('Test')
logger.addHandler(logging.StreamHandler())

@orca.injectable()
def inj1() -> str:
    return 'INJ 1'

@orca.injectable()
def inj2():
    return 'INJ 2'

@orca.injectable()
def inj_int() -> int:
    return 42

@orca.injectable()
def inj_list() -> List[int]:
    return [2, 3, 66]

@orca.injectable()
def inj_dict():
    return dict(a=1, b=-1)

@group(groupname='Hallo')
@orca.step()
def step1(inj_list):
    """dummy step"""
    sleep(5)

@group(groupname='Hallo')
@orca.step()
def step2(inj1, inj2):
    """another dummy step"""
    sleep(5)

@group(groupname='Huhu')
@orca.step()
def step_dict(inj_dict):
    """another dummy step"""
    for k, v in inj_dict.items():
        logger.info(f'{k}: {v}')
        sleep(1)
