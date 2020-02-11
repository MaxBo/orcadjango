import orca
from typing import List, Dict
from time import sleep
import pandas as pd
import xarray as xr
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


@group(groupname='strings', order=2)
@orca.injectable()
def inj12(inj1: str, inj2: str) -> str:
    return f'{inj1} -> {inj2}'


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
def inj_dict() -> Dict[str, int]:
    return dict(a=1, b=-1)


@group('data')
@orca.injectable()
def dataframe() -> pd.DataFrame:
    """Pandas Dataframe"""
    df = pd.DataFrame([['AAA', 3, 5.6], ['BBB', 6, -4.3]],
                      columns=['Col1', 'Col2', 'Col3'])
    return df


@group('data')
@orca.injectable()
def dataset(dataframe: pd.DataFrame) -> xr.Dataset:
    """xarray.Dataset"""
    ds = dataframe.to_xarray()
    return ds


@group('data')
@orca.injectable()
def dataarray(dataset: xr.Dataset) -> xr.DataArray:
    """xarray.DataArray"""
    da = dataset['Col1']
    return da


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
def step1(inj_list, dataframe):
    """dummy step"""
    sleep(5)


@group(groupname='Huhu')
@orca.step()
def step_dict(inj_dict):
    """another dummy step with dict"""
    for k, v in inj_dict.items():
        logger.info(f'{k}: {v}')
        sleep(1)
