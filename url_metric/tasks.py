__author__ = 'margus'

from celery.task import task, periodic_task
from celery.schedules import crontab
import datetime
from django.conf import settings

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

@task(name="url_metric.metric")
def metric(metric_name, value=1):
    exporter = exports.get_exporter()
    exporter.metric(metric_name, value)


@periodic_task(run_every=crontab(hour=0, minute=5), name="url_metric.export_host_data")
def export_host_data(report_date=None):
    if not report_date:
        report_date = datetime.date.today() - datetime.timedelta(days=1)


    exporter = exports.get_exporter()
    report_data = models.HostCounter.objects.filter(date=report_date)
    for data in report_data:
        key = "Host.%s" % data.hostname
        exporter.export(key, data.count)

    exporter.save()
