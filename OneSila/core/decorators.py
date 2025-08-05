from datetime import datetime
from functools import wraps
from django.db import transaction

import logging
logger = logging.getLogger(__name__)


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


def track_time(logger, default_msg=''):
    """
    Measure execution time of the wrapped function and log it.

    TODO: switch to logger.info once info logs are visible.
    """
    def deco_timeit(f):

        @wraps(f)
        def f_timeit(*args, **kwargs):
            start = datetime.now()
            result = f(*args, **kwargs)
            stop = datetime.now()
            msg = f"{default_msg} {f.__name__} took {stop - start}" if default_msg else f"{f.__name__} took {stop - start}"
            logger.error(msg)  # TODO: use logger.info when logging configuration is fixed
            return result

        return f_timeit

    return deco_timeit


def trigger_pre_and_post_save(dirty_field, signal_pre=None, signal_post=None):
    """
    Trigger a pre-save and post-save signal on the save method.
    """
    def deco(f):

        @wraps(f)
        def f_wrap(self, *args, **kwargs):
            is_dirty_field = False
            if self.is_dirty_field(dirty_field):
                is_dirty_field = True
                if signal_pre is not None:
                    signal_pre.send(sender=self.__class__, instance=self)

            fn = f(self, *args, **kwargs)

            if is_dirty_field:
                if signal_post is not None:
                    signal_post.send(sender=self.__class__, instance=self)

            return fn

        return f_wrap

    return deco


def trigger_signal_for_dirty_fields(*fields):
    """
    Decorator to execute a post save / create / update signal only if a specified field is dirty.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(sender, instance, *args, **kwargs):
            # Check if any of the specified fields are dirty
            if any(instance.is_dirty_field(field) for field in fields):
                return f(sender, instance, *args, **kwargs)
            # If none of the fields are dirty, do nothing
            return None
        return wrapper
    return decorator


def run_task_after_commit(task_func):
    """
    Decorator to wrap any @db_task() to ensure it runs only after the outer transaction commits.
    Safe to use globally — runs immediately if there's no transaction.
    """
    @wraps(task_func)
    def wrapper(*args, **kwargs):
        transaction.on_commit(lambda: task_func(*args, **kwargs))

    return wrapper


def log_method_calls(cls):
    """"Use this decorator to log which methods are being called
    from a class.  This is a class decorator"""
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and not attr_name.startswith("__"):
            setattr(cls, attr_name, log_wrapper(attr))
    return cls


def log_wrapper(method):
    def wrapped(*args, **kwargs):
        logger.debug(f"Called: {method.__qualname__}({args[1:]}, {kwargs})")
        return method(*args, **kwargs)
    return wrapped


def soft_fail():
    """
    Decorator that catches any exceptions, logs them to the error log,
    and returns None instead of raising the exception.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
                return None
        return wrapper
    return decorator
