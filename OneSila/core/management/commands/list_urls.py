from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.urls import URLPattern, URLResolver


def list_urls(pattern_list, acc=[]):
    try:
        pattern = pattern_list[0]
    except IndexError:
        return

    if isinstance(pattern, URLPattern):
        yield acc + [str(pattern.pattern), pattern.name]
    elif isinstance(pattern, URLResolver):
        yield from list_urls(pattern.url_patterns, acc + [str(pattern.pattern)])

    yield from list_urls(pattern_list[1:], acc)


class Command(BaseCommand):
    help = 'List all URLs from the urlconf, for a given app or all.'

    def add_arguments(self, parser):
        parser.add_argument("-ia", "--include-admin",
            action="store_true",
            help="Include admin app"
                            )

    def handle(self, *args, **options):
        include_admin = options['include_admin']

        urlconf = __import__(settings.ROOT_URLCONF, {}, {}, [''])

        records, glen, nlen = [], 0, 0

        url_list = []
        for i in list_urls(urlconf.urlpatterns):
            app = i[0].lstrip('/')

            if 'admin' in app and not include_admin:
                pass
            else:
                url_list.append(i)

        for p in url_list:
            app = p[0].rstrip('/').replace('-', '_')

            if not app:
                app = 'core'

            if 'admin' in app and not include_admin:
                pass
            else:
                reverse_str = f"{app}:{p[-1]}"
                url_path = ''.join(p[:-1])

                record = [url_path, reverse_str]

                # # Update me, or add an argument
                # if record[0].startswith('contacts'):
                try:
                    clen = len(record[0])
                    if clen > glen:
                        glen = clen

                    clen = len(record[1])
                    if clen > nlen:
                        nlen = clen
                except TypeError:
                    pass

                records.append(record)

        self.stdout.write('{:-<{width}}'.format('', width=glen + nlen))
        self.stdout.write('{:<{glen}}Name'.format('Path', glen=glen + 4))
        self.stdout.write('{:-<{width}}'.format('', width=glen + nlen))

        for record in records:
            self.stdout.write('{path:<{glen}}{name}'.format(path=record[0],
                name=record[1],
                glen=glen + 4))

        self.stdout.write('{:-<{width}}'.format('', width=glen + nlen))
