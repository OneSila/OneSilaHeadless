import traceback
from functools import wraps
import inspect

def handle_import_exception(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            if self.import_process.skip_broken_records:
                sig = inspect.signature(func)
                bound_args = sig.bind(self, *args, **kwargs)
                bound_args.apply_defaults()

                # Find first argument containing 'data' in its name
                record_data = None
                for key, value in bound_args.arguments.items():
                    if 'data' in key and key != 'self':
                        record_data = value
                        break
                # Fallback to first positional argument after 'self'
                if record_data is None:
                    all_args = list(bound_args.arguments.items())
                    if len(all_args) > 1:
                        record_data = all_args[1][1]

                step_name = kwargs.get('step_name', func.__name__)
                record = {
                    'step': step_name,
                    'data': record_data,
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                }
                self._broken_records.append(record)
            else:
                raise

    return wrapper

