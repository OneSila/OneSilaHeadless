import os
import random
import string
from functools import partial


def _tenant_upload_to(instance, filename, subdir, depth=5, segment_length=2):
    """Build a randomized path rooted at the tenant's company ID."""
    company_id = getattr(instance, "multi_tenant_company_id", None)
    if company_id is None:
        company = getattr(instance, "multi_tenant_company", None)
        company_id = getattr(company, "id", "unknown")
    segments = [
        "".join(random.choices(string.ascii_lowercase + string.digits, k=segment_length))
        for _ in range(depth)
    ]
    return os.path.join(str(company_id), subdir, *segments, filename)


def tenant_upload_to(subdir, depth=3, segment_length=2):
    """Return a callable suitable for Django's ``upload_to`` argument."""
    return partial(_tenant_upload_to, subdir=subdir, depth=depth, segment_length=segment_length)
