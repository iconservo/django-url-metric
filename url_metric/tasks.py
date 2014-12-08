__author__ = 'margus'

from celery.task import task, periodic_task
from celery.schedules import crontab
import datetime

from url_metric import models, exports

@task(name="url_metric.increase_host_count")
def increase_host_count(hostname):
    now = datetime.date.today()
    result = models.HostCounter.objects.filter(hostname=hostname, date=now).first()
    if not result:
        result = models.HostCounter()
        result.hostname = hostname
        result.date = now
        result.count = 1
    else:
        result.count += 1

    result.save()

@periodic_task(run_every=crontab(hour=0, minute=5), name="url_metric.export_host_data")
def export_host_data(report_date=None):
    if not report_date:
        report_date = datetime.date.today()


    exporter = exports.get_exporter()
    report_data = models.HostCounter.objects.filter(date=report_date)
    for data in report_data:
        exporter.export("url.request", data.count, data.hostname)

    exporter.save()
