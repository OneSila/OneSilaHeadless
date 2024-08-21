from django.conf import settings
from django.http import HttpResponse
import os
from get_absolute_url.helpers import reverse_lazy
from io import BytesIO


def get_languages():
    return settings.LANGUAGES


def save_test_file(filename, file_contents):
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
        raise Exception('Content-Type for extension {} unkown'.format(extension))

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
