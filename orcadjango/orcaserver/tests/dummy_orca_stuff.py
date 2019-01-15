import orca
from time import sleep


@orca.injectable()
def inj1():
    return 'INJ 1'


@orca.injectable()
def inj2():
    return 'INJ 2'


@orca.step()
def step1():
    """dummy step"""
    sleep(5)


@orca.step()
def step2():
    """another dummy step"""
    sleep(5)

