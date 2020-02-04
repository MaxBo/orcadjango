import orca
from typing import List
from time import sleep
from orcadjango.decorators import group
import logging
logger = logging.getLogger('OrcaLog')
logger.addHandler(logging.StreamHandler())

@group(groupname='strings')
@orca.injectable()
def inj1() -> str:
    return 'INJ 1'

@group(groupname='strings')
@orca.injectable()
def inj2():
    return 'INJ 2'

@group(groupname='ints')
@orca.injectable()
def inj_int() -> int:
    return 42

@group(groupname='ints')
@orca.injectable()
def inj_list() -> List[int]:
    return [2, 3, 66]

@group(groupname='das dict')
@orca.injectable()
def inj_dict():
    return dict(a=1, b=-1)

@group(groupname='Hallo')
@orca.step()
def step1(inj_list):
    """dummy step"""
    sleep(5)

from contextlib import ContextDecorator
class mycontext(ContextDecorator):
    def __enter__(self):
        print('Starting')
        return self

    def __exit__(self, *exc):
        print('Finishing')
        return False

@group(groupname='Hallo')
@orca.step()
def step2(inj1, inj2):
    """another dummy step"""
    with mycontext():
        print('start')
        for i in range(10):
            sleep(1)
            print(i)
    #except Exception as e:
        #print(str(e))
    #finally:
        #print('finally')

@group(groupname='Huhu')
@orca.step()
def step_dict(inj_dict):
    """another dummy step"""
    for k, v in inj_dict.items():
        logger.info(f'{k}: {v}')
        sleep(1)

#class ScenarioTemplate:
    #def __init__(self, step_list, injectable_values):
        #self.step_list = step_list
        #self.injectable_values = injectable_values

#@orca.scenario_config(name='OTP Routing')
#def otp_steps():
    #template =  ScenarioTemplate(
        #[step1,
         #step2,
         #],
        #dict(inj_int= 33))
    #return template