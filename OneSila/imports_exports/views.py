from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.views import View

from imports_exports.models import Export

class DirectExportFeedView(View):
    def get(self, request, feed_key):
        authorization = str(request.headers.get("Authorization", "") or "").strip()
        if not authorization.startswith("Bearer "):
            return HttpResponseForbidden("Missing bearer token.")

        token = authorization.split(" ", 1)[1].strip()
        if not token:
            return HttpResponseForbidden("Missing bearer token.")

        export = Export.objects.filter(
            feed_key=feed_key,
            type=Export.TYPE_JSON_FEED,
            status=Export.STATUS_SUCCESS,
        ).first()
        if export is None:
            raise Http404("Export feed not found.")

        return JsonResponse(export.raw_data, safe=not isinstance(export.raw_data, list))
