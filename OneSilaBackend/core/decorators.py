from datetime import datetime
from functools import wraps


def timeit_and_log(logger, default_msg='', print_logger=False):
    '''
    run a timer on a function, and log it, prepending the default_msg
    '''
    def deco_timeit(f):

        @wraps(f)
        def f_timeit(*args, **kwargs):
            # Start the timer before running the function
            start = datetime.now()

            # Run the function and save the result
            fn = f(*args, **kwargs)

            # Stop the timer and prep the log message
            stop = datetime.now()
            msg = f"{default_msg} {f.__name__} took {stop - start}"
            logger.info(msg)
            if print_logger:
                print(msg)

            return fn

        return f_timeit  # true decorator

    return deco_timeit
