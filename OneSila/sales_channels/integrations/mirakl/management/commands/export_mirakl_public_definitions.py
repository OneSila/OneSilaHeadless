from django.core.management.base import BaseCommand, CommandError

from sales_channels.integrations.mirakl.utils.public_definitions import helpers as public_definition_helpers


class Command(BaseCommand):
    help = "Export Mirakl public definitions into mirakl/utils/public_definitions/."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Suffix used in the exported file name.")

    def handle(self, *args, **options):
        try:
            file_name = public_definition_helpers.build_export_filename(
                name=options["name"],
            )
            file_path = public_definition_helpers.get_public_definitions_file_path(
                file_name=file_name,
                create_directory=True,
            )
            exported_count = public_definition_helpers.export_public_definitions_to_file(
                file_path=file_path,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {exported_count} Mirakl public definitions to {file_path.name}."
            )
        )
