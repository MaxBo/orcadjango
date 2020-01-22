import orca
from time import sleep


@orca.injectable()
def inj1():
    return 'INJ 1'


@orca.injectable()
def inj2():
    return 'INJ 2'


@orca.injectable()
def inj_int():
    return 42


@orca.injectable()
def inj_list():
    return [2, 3, 66]


@orca.injectable()
def inj_dict():
    return dict(a=1, b=-1)


@orca.step()
def step1(inj_list):
    """dummy step"""
    sleep(5)


@orca.step()
def step2(inj1, inj2):
    """another dummy step"""
    sleep(5)


@orca.step()
def step_dict(inj_dict):
    """another dummy step"""
    for k, v in inj_dict.items():
        print(k, v)
