from orca import logger as orca_logger

class DummySub:
    def __init__(self, logger=None):
        self.logger = logger or orca_logger

    def run(self):
        self.logger.info('test_sub')