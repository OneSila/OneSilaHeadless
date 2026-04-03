from django.http import FileResponse, Http404, HttpResponseForbidden
from django.views import View

from imports_exports.models import Export

class DirectExportFeedView(View):
    def get(self, request, feed_key):
        # authorization = str(request.headers.get("Authorization", "") or "").strip()
        # if not authorization.startswith("Bearer "):
        #     return HttpResponseForbidden("Missing bearer token.")
        #
        # token = authorization.split(" ", 1)[1].strip()
        # if not token:
        #     return HttpResponseForbidden("Missing bearer token.")

        export = Export.objects.filter(
            feed_key=feed_key,
            type=Export.TYPE_JSON_FEED,
            status=Export.STATUS_SUCCESS,
        ).first()
        if export is None or not export.file:
            raise Http404("Export feed not found.")

        return FileResponse(
            export.file.open("rb"),
            content_type="application/json",
            as_attachment=False,
            filename=export.file.name.rsplit("/", 1)[-1],
        )
