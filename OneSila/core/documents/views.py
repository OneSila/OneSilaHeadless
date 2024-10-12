from strawberry.relay import to_base64, from_base64

from core.views import EmptyTemplateView
from core.helpers import single_file_httpresponse


class DocumentView(EmptyTemplateView):
    # model = MyModel
    print_method = 'print'

    def from_global_id(self, global_id):
        return from_base64(global_id)

    def get(self, request, pk, *args, **kwargs):

        if not pk.isdigit():
            _, pk = self.from_global_id(pk)

        instance = self.model.objects.get(pk=pk)
        filename, filedata = getattr(instance, self.print_method)()
        return single_file_httpresponse(filedata=filedata, filename=filename)
