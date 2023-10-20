from datetime import datetime
from functools import wraps


def timeit_and_log(logger, default_msg='', print_logger=False):
    '''
    run a timer on a function, and log it, prepending the default_msg.
    Useful for figuring out performance issues in factories.
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

        return f_timeit

    return deco_timeit


def trigger_pre_and_post_save(dirty_field, signal_pre, signal_post):
    """
    Trigger a pre-save and post-save signal on the save method.
    """
    def deco(f):

        @wraps(f)
        def f_wrap(self, *args, **kwargs):
            is_dirty_field = False
            if self.is_dirty_field(field):
                is_dirty_field = True
                signal_pre.send(sender=self.__class__, instance=self)

            fn = f(self, *args, **kwargs)

            if is_dirty_field:
                signal_post.send(sender=self.__class__, instance=self)

            return fn

        return f_wrap

    return deco
