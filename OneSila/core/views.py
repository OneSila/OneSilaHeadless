from django.views.generic import TemplateView


class EmptyTemplateView(TemplateView):
    template_name = "core/empty_template_view.html"
