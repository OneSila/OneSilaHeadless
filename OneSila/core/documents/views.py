from core.views import EmptyTemplateView
from core.helpers import single_file_httpresponse


class DocumentViev(EmptyTemplateView):
    # model = MyModel
    print_method = 'print'

    def get(self, request, pk, *args, **kwargs):
        instance = self.model.objects.get(pk=pk)
        filename, filedata = getattr(instance, self.print_method)()
        return single_file_httpresponse(filedata=filedata, filename=filename)
