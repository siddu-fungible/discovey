from django.core.management.base import BaseCommand, CommandError
from web.tools.models import Session

class Command(BaseCommand):
    help = 'Initialize'

    def handle(self, *args, **options):
        if not Session.objects.count():
            s = Session()
            s.save()
            self.stdout.write(self.style.SUCCESS('Successfully created tables'))
