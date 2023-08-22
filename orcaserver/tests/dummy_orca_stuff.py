import orca
from typing import List, Dict
from time import sleep
import pandas as pd
import xarray as xr
from orcadjango.decorators import meta
from orca import logger

from .dummy_submodule import DummySub


@meta(group='strings', order=1)
@orca.injectable()
def inj1() -> str:
    """string"""
    return 'INJ 1'


@meta(group='strings', order=2)
@orca.injectable()
def inj2():
    """string"""
    return 'INJ 2'


@meta(group='strings', order=2)
@orca.injectable()
def inj12(inj1: str, inj2: str) -> str:
    """composed"""
    return f'{inj1} -> {inj2}'


@meta(group='ints', order=2)
@orca.injectable()
def inj_int() -> int:
    """integer"""
    return 42


@meta(group='ints', order=1)
@orca.injectable()
def inj_list() -> List[int]:
    """list"""
    return [2, 3, 66]


@meta(group='ints', order=3, choices=[1, 2, 3])
@orca.injectable()
def inj_int_choose_many() -> List[int]:
    """choose many out of list, one default is not in list"""
    return [45, 2]


@meta(group='ints', order=4, choices=[34, 45, 12])
@orca.injectable()
def inj_int_choose_one() -> int:
    """choose one out of list, default is not in list"""
    return 345


@meta(group='das dict')
@orca.injectable()
def inj_dict() -> Dict[str, int]:
    """dictionary"""
    return dict(a=1, b=-1)


@meta(group='data')
@orca.injectable()
def dataframe() -> pd.DataFrame:
    """Pandas Dataframe"""
    df = pd.DataFrame([['AAA', 3, 5.6], ['BBB', 6, -4.3]],
                      columns=['Col1', 'Col2', 'Col3'])
    return df


@meta(group='data')
@orca.injectable()
def dataset(dataframe: pd.DataFrame) -> xr.Dataset:
    """xarray.Dataset"""
    ds = dataframe.to_xarray()
    return ds


@meta(group='data')
@orca.injectable()
def dataarray(dataset: xr.Dataset) -> xr.DataArray:
    """xarray.DataArray"""
    da = dataset['Col1']
    return da


from contextlib import ContextDecorator


class mycontext(ContextDecorator):
    def __enter__(self):
        logger.info('Starting')
        return self

    def __exit__(self, *exc):
        logger.info('Finishing')
        return False


@meta(group='Hallo', order=2)
@orca.step()
def step2(inj1, inj2):
    """another dummy step"""
    with mycontext():
        for i in range(10):
            logger.info(f'loop {i}')
            logger.warning(f'sleeping')
            sleep(1)
            print(i)

    logger.error(f'Test error message')


@meta(group='Hallo', order=1)
@orca.step()
def step1(inj_list, dataframe):
    """dummy step"""
    dummy = DummySub(logger=logger)
    dummy.run()
    sleep(5)
    logger.info('step1 finished')


@meta(group='Hallo', order=2)
@orca.step()
def error_step():
    """this step will fail"""
    raise Exception('planned error')


@meta(group='Huhu')
@orca.step()
def step_dict(inj_dict):
    """another dummy step with dict"""
    for k, v in inj_dict.items():
        logger.info(f'{k}: {v}')
        sleep(1)


@meta(group='Huhu')
@orca.step()
def step_multiply_df(inj_int, dataframe):
    a = dataframe.copy()
    for i in range(inj_int-1):
        dataframe += a
        logger.info(i)
        #print(id(dataframe))
        #print(f'{id(logger)} {i}')
        sleep(1)