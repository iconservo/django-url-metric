__author__ = 'margus'

from django.core.management.base import BaseCommand, CommandError
from url_metric.tasks import send_host_data

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        send_host_data()