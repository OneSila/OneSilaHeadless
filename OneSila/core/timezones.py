from pytz import common_timezones_set

# https://stackoverflow.com/a/13867319/5731101
TIMEZONE_CHOICES = sorted([(i, i) for i in common_timezones_set])
DEFAULT_TIMEZONE = 'Europe/London'
