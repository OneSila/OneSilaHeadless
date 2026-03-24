from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sales_channels.integrations.mirakl.utils.public_definitions import helpers as public_definition_helpers


class Command(BaseCommand):
    help = "Import Mirakl public definitions from mirakl/utils/public_definitions/."

    def add_arguments(self, parser):
        parser.add_argument("file_name", help="File name inside mirakl/utils/public_definitions/.")
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Create new definitions but leave existing hostname/property_code pairs untouched.",
        )

    def handle(self, *args, **options):
        try:
            file_path = public_definition_helpers.get_public_definitions_file_path(
                file_name=options["file_name"],
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if not file_path.exists():
            raise CommandError(f"File '{file_path.name}' does not exist in {file_path.parent}.")

        try:
            with transaction.atomic():
                stats = public_definition_helpers.import_public_definitions_from_file(
                    file_path=file_path,
                    skip_existing=bool(options["skip_existing"]),
                )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Imported Mirakl public definitions from "
                f"{file_path.name}: created={stats['created']}, updated={stats['updated']}, skipped={stats['skipped']}."
            )
        )
