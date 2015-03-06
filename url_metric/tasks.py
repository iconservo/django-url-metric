__author__ = 'margus'

from celery.task import task, periodic_task
from celery.schedules import crontab
import datetime
import logging

from url_metric import models, exports

@task(name="url_metric.increase_host_count_task")
def increase_host_count_task(hostname):
    """
    Increases host count in database (for now)
    :param hostname:
    :return:
    """
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


def increase_host_count_metric(hostname):
    """
    Increases host count directly in metric
    Useful when there are too many remote queries
    :param hostname:
    :return:
    """
    metric_name = "Host.%s" % hostname
    exporter = exports.get_exporter()
    if exporter:
        exporter.metric(metric_name, 1)


@task(name="url_metric.metric")
def metric(metric_name, value=1, hostname = None):
    result = None
    logger_host = ""
    if hostname:
        logger_host = ".%s" % hostname

    try:
        exporter = exports.get_exporter()
        debug_logger = logging.getLogger('external.debug%s' % logger_host)
        if exporter:
            result = exporter.metric(metric_name, 1)
            debug_logger.debug("source: %s %s +%s" % (exporter.source, metric_name, value))
        else:
            debug_logger.debug("exporter: %s" % exporter)

    except Exception, e:
        error_logger = logging.getLogger('external.error%s' % logger_host)
        error_logger.exception(metric_name)

    return result

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
