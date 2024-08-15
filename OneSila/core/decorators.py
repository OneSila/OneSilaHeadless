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