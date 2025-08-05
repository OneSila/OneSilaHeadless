from functools import wraps
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class AddLogTimeentry:
    def _set_logger(self, logger):
        self.add_log_time_entry_logger = logger

    def _set_start_time(self):
        self.start_time = timezone.now()
        self.add_log_time_entry_logger.debug(f"Start timer for {self.__class__.__name__} at {self.start_time}")

    def get_log_message(self, message):
        return f"{self.__class__.__name__}__{message} took {timezone.now() - self.start_time}"

    def _add_log_entry(self, message):
        self.add_log_time_entry_logger.debug(self.get_log_message(message))
        self._set_start_time()


def timeit_and_log(logger, default_msg='', print_logger=False):
    '''
    run a timer on a function, and log it, prepending the default_msg.
    Useful for figuring out performance issues in factories.
    '''
    def deco_timeit(f):

        @wraps(f)
        def f_timeit(*args, **kwargs):
            # Start the timer before running the function
            start = timezone.now()

            # Run the function and save the result
            fn = f(*args, **kwargs)

            # Stop the timer and prep the log message
            stop = timezone.now()
            msg = f"{default_msg} {f.__name__} took {stop - start}"
            logger.info(msg)
            if print_logger:
                print(msg)

            return fn

        return f_timeit

    return deco_timeit
