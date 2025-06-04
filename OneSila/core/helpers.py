import json

from django.conf import settings
from django.http import HttpResponse
import os
from get_absolute_url.helpers import reverse_lazy
from io import BytesIO
import zipfile


def get_languages():
    return settings.LANGUAGES


def is_or_create_folder(path):
    if not os.path.isdir(path):
        os.mkdir(path)


def save_test_file(filename, file_contents):
    is_or_create_folder(settings.SAVE_TEST_FILES_ROOT)
    filepath = os.path.join(settings.SAVE_TEST_FILES_ROOT, filename)
    with open(filepath, 'wb') as f:
        f.write(file_contents)

    return filepath


def return_extension(filename_or_path):
    return filename_or_path.split('.')[-1].lower()


def multiple_files_to_zip_httpresponse(files, zip_filename):
    '''
    return a HttpResponse with multiple files in zip format
    :param files: dict with {document_filename: data_in_bytes}
    :param zip_filename: string as 'zip_filename' without extension.
    '''
    outfile = BytesIO()
    with zipfile.ZipFile(outfile, 'w') as zf:
        for k, v in files.items():
            zf.writestr(k, v)

    response = HttpResponse(outfile.getvalue(), content_type="application/octet-stream")
    response['Content-Disposition'] = u'attachment; filename={}.zip'.format(zip_filename)
    return response


def single_file_httpresponse(filedata, filename):
    '''
    return a HttpResponse with a single file
    :param filedata: data to write
    :param filename: string as 'filename.pdf'
    Currently only supporting pdf, csv and xlsx-files
    '''
    extension = return_extension(filename)

    content_types = {
        'pdf': 'application/pdf',
        'csv': 'text/csv',
        'json': 'application/json',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    try:
        content_type = content_types[extension]
    except KeyError:
        raise TypeError(f'Unkown Content-Type for extension {extension}')

    response = HttpResponse(content_type=content_type)

    if extension == 'pdf':
        response['Content-Disposition'] = u'inline;filename="{}"'.format(filename)
    else:
        response['Content-Disposition'] = u'attachment; filename="{}"'.format(filename)

    response.write(filedata)
    return response


def dynamic_file_httpresponse(files, zip_filename):
    '''
    return a HttpResponse with a single files, or
    multiple files in zip format
    :param files: dict with {document_filename: data}
    :param zip_filename: string as 'zip_filename' without extension
    '''
    if len(files) == 1:
        filename, filedata = list(files.items())[0]
        return single_file_httpresponse(filedata, filename)
    else:
        return multiple_files_to_zip_httpresponse(files, zip_filename)


def get_nested_attr(instance, attr_path):
    """
    Retrieves the value of a nested attribute from an instance.

    :param instance: The object to retrieve the attribute from.
    :param attr_path: A string representing the path to the attribute, using '__' to denote nesting.
    :return: The value of the nested attribute, or None if any part of the path is not found.
    """
    try:
        for attr in attr_path.split('__'):
            instance = getattr(instance, attr, None)
            if instance is None:
                return None
        return instance
    except AttributeError:
        return None


def clean_json_data(data):
    """
    Recursively cleans the data to remove or transform non-serializable objects.
    """
    if isinstance(data, dict):
        return {k: clean_json_data(v) for k, v in data.items() if is_json_serializable(v)}
    elif isinstance(data, list):
        return [clean_json_data(item) for item in data]
    else:
        return data if is_json_serializable(data) else str(data)


def is_json_serializable(value):
    """
    Checks if a value is JSON-serializable.
    """
    try:
        json.dumps(value)
        return True
    except (TypeError, OverflowError):
        return False


def safe_run_task(task_func, *args, **kwargs):
    from django.db import transaction, connection

    if connection.in_atomic_block:
        transaction.on_commit(lambda: task_func(*args, **kwargs))
    else:
        task_func(*args, **kwargs)
