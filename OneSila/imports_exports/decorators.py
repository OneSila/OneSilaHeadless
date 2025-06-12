import traceback
from functools import wraps

def handle_import_exception(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:

            if self.import_process.skip_broken_records:

                step_name = kwargs.get('step_name', func.__name__)
                record = {
                    'step': step_name,
                    'data': args[0] if args else None,
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                }

                self._broken_records.append(record)
            else:
                raise
    return wrapper
