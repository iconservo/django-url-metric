"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, LiveServerTestCase
from django.test.utils import override_settings
from url_metric import exports, custom_opener, models
from django.core.cache import cache

from django.conf import settings


class SimpleTest(TestCase):
    def test_get_exporter_none(self):
        exporter = exports.get_exporter()
        self.assertIsNone(exporter, "There should not be an url metric")


    @override_settings(URL_METRIC_EXPORT_ENGINE="librato",
                       URL_METRIC_LIBRATO_USER="test",
                        URL_METRIC_LIBRATO_TOKEN="test")
    def test_get_exporter(self):
        exporter = exports.get_exporter()
        self.assertIsNotNone(exporter, "There should be an url metric")

    @override_settings(URL_METRIC_EXPORT_ENGINE="librato",
                       URL_METRIC_LIBRATO_USER="test",
                       URL_METRIC_LIBRATO_TOKEN="test",
                       URL_METRIC_SOURCE="testing")
    def test_exporter_source(self):
        exporter = exports.get_exporter()
        self.assertIsNotNone(exporter, "There should be an url metric")
        self.assertEqual(exporter.source, "testing")

    @override_settings(CELERY_ALWAYS_EAGER=True,
                       TEST_RUNNER='djcelery.contrib.test_runner.CeleryTestSuiteRunner')
    def test_urllib2(self):
        custom_opener.urlopen("http://www.bing.com/")
        model = models.HostCounter.objects.filter(hostname="www.bing.com").first()
        self.assertIsNotNone(model, "Unable to find proper model")
        self.assertEqual(model.count, 1, "www.bing.com is not accessed 1 time. Found %s times instead" % model.count)

    @override_settings(CELERY_ALWAYS_EAGER=True,
                       TEST_RUNNER='djcelery.contrib.test_runner.CeleryTestSuiteRunner')
    def test_requests(self):
        custom_opener.get("http://www.bing.com/")
        model = models.HostCounter.objects.filter(hostname="www.bing.com").first()
        self.assertIsNotNone(model, "Unable to find proper model")
        self.assertEqual(model.count, 1, "www.bing.com is not accessed 1 time. Found %s times instead" % model.count)

    @override_settings(URL_METRIC_EXPORT_ENGINE="dummy",
                       CELERY_ALWAYS_EAGER=True,
                       URL_METRIC_HOST_OVERRIDES = {
                            'maps.googleapis.com/maps/api/timezone/json': ("maps.googleapis.com.TimeZone", custom_opener.get_geocode_api_status),
                            'maps.google.com/maps/api/elevation/json': ("maps.google.com.Elevation", custom_opener.get_geocode_api_status),
                            'maps.googleapis.com/maps/api/geocode/json': ("maps.googleapis.com.GeoCode", custom_opener.get_geocode_api_status),
                        })
    def test_metric(self):
        from url_metric.tasks import metric

        exports.DummyExporter.clear_metrics()
        #custom_opener.urlopen("http://pubsub.pubnub.com/publish/pub-c-3083fedb-f124-44d2-a16b-74387d507a20/sub-c-b5b5eaae-8cd9-11e3-a56b-02ee2ddab7fe/fef4b684033fd6a0d536b492bbf2f657/channel_viljar_test/0/123")
        metric_name = "External.%s.%s.%s" % ('Testing', 'GET', 200)
        metric.delay(metric_name)
        self.assertDictEqual(exports.DummyExporter.instance.metrics, {'External.Testing.GET.200': 1})

        exports.DummyExporter.clear_metrics()
        response = custom_opener.urlopen("https://maps.googleapis.com/maps/api/geocode/json?&sensor=false&latlng=37.5217949,-122.2802549")
        self.assertEqual(response.code, 200)

        response = custom_opener.urlopen("http://maps.google.com/maps/api/elevation/json?sensor=true&locations=34.239056,-116.948547")
        self.assertEqual(response.code, 200)

        response = custom_opener.urlopen("https://maps.googleapis.com/maps/api/timezone/json?&sensor=true&&location=34.239056,-116.948547&timestamp=1425641887.25")
        self.assertEqual(response.code, 200)

        self.assertDictEqual(exports.DummyExporter.instance.metrics, {
                'External.maps.googleapis.com.TimeZone.GET.200.OK': 1,
                'External.maps.googleapis.com.GeoCode.GET.200.OK': 1,
                'External.maps.google.com.Elevation.GET.200.OK': 1
            }
        )

        exports.DummyExporter.clear_metrics()
        response = custom_opener.get("https://maps.googleapis.com/maps/api/timezone/json?&sensor=true&&location=34.239056,-116.948547&timestamp=1425641887.25")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(exports.DummyExporter.instance.metrics, {'External.maps.googleapis.com.TimeZone.GET.200.OK': 1})

class RedisExporterTest(TestCase):
    @override_settings(URL_METRIC_EXPORT_ENGINE="redis",
                       URL_METRIC_LIBRATO_USER="test",
                       URL_METRIC_LIBRATO_TOKEN="test",
                       URL_METRIC_SOURCE="testing")
    def test_redis_db_and_cache(self):
        expected_cache_metrics = ['testing:gauge:RedisTest', 'testing:gauge:RedisTest2']

        exporter = exports.get_exporter()
        exporter.clean_cache()
        for m_key in expected_cache_metrics:
            self.assertFalse(cache.has_key(m_key))

        exporter.gauge('RedisTest', 1)

        env_metrics = exporter.get_environment_metrics()
        self.assertEqual(len(env_metrics), 1)
        metric_name = env_metrics[0]
        self.assertEqual(metric_name, expected_cache_metrics[0])

        self.assertTrue(cache.has_key(metric_name))
        metric_count = cache.get(metric_name)
        self.assertEqual(metric_count, 1)

        exporter.gauge('RedisTest', 10)
        env_metrics = exporter.get_environment_metrics()
        self.assertEqual(len(env_metrics), 1)
        metric_count = cache.get(metric_name)
        self.assertEqual(metric_count, 11)

        exporter.gauge('RedisTest2', 3)
        env_metrics = exporter.get_environment_metrics()
        self.assertEqual(len(env_metrics), 2)

        self.assertTrue(env_metrics[0] in expected_cache_metrics)
        self.assertTrue(env_metrics[1] in expected_cache_metrics)

        metric_count = cache.get(env_metrics[0])
        self.assertEqual(metric_count, 11)

        metric_count = cache.get(env_metrics[1])
        self.assertEqual(metric_count, 3)

        exporter.save(commit=False)

        env_metrics = exporter.get_environment_metrics()
        self.assertEqual(len(env_metrics), 0)
        for m_key in expected_cache_metrics:
            self.assertFalse(cache.has_key(m_key))

    @override_settings(URL_METRIC_EXPORT_ENGINE="redis",
                       URL_METRIC_LIBRATO_USER="test",
                       URL_METRIC_LIBRATO_TOKEN="test",
                       URL_METRIC_SOURCE="testing",
                       URL_METRIC_HOST_OVERRIDES = {
                            'maps.googleapis.com/maps/api/timezone/json': ("maps.googleapis.com.TimeZone", custom_opener.get_geocode_api_status),
                            'maps.google.com/maps/api/elevation/json': ("maps.google.com.Elevation", custom_opener.get_geocode_api_status),
                            'maps.googleapis.com/maps/api/geocode/json': ("maps.googleapis.com.GeoCode", custom_opener.get_geocode_api_status),
                        },
                       CELERY_ALWAYS_EAGER=True,
                       TEST_RUNNER='djcelery.contrib.test_runner.CeleryTestSuiteRunner'
    )
    def test_metric(self):
        from url_metric.tasks import export_metric_data
        expected_cache_metrics = [
            'testing:gauge:External.Testing.GET.200',
            'testing:gauge:External.maps.googleapis.com.TimeZone.GET.200.OK',
            'testing:gauge:External.maps.googleapis.com.GeoCode.GET.200.OK',
            'testing:gauge:External.maps.google.com.Elevation.GET.200.OK',
        ]

        exporter = exports.get_exporter()
        exporter.clean_cache()

        metric_name = "External.%s.%s.%s" % ('Testing', 'GET', 200)
        exporter.metric(metric_name)
        env_metrics = exporter.get_environment_metrics()
        self.assertEqual(len(env_metrics), 1)

        self.assertTrue(env_metrics[0] in expected_cache_metrics)

        exporter.clean_cache()
        response = custom_opener.urlopen("https://maps.googleapis.com/maps/api/geocode/json?&sensor=false&latlng=37.5217949,-122.2802549")
        self.assertEqual(response.code, 200)

        response = custom_opener.urlopen("http://maps.google.com/maps/api/elevation/json?sensor=true&locations=34.239056,-116.948547")
        self.assertEqual(response.code, 200)

        response = custom_opener.urlopen("https://maps.googleapis.com/maps/api/timezone/json?&sensor=true&&location=34.239056,-116.948547&timestamp=1425641887.25")
        self.assertEqual(response.code, 200)

        env_metrics = exporter.get_environment_metrics()
        self.assertEqual(len(env_metrics), 3)
        for metric in env_metrics:
            metric_value = cache.get(metric, -1)
            self.assertEqual(metric_value, 1)

        old_env_metrics = env_metrics

        exporter.save(commit=False)
        #export_metric_data.delay()

        env_metrics = exporter.get_environment_metrics()
        self.assertEqual(len(env_metrics), 0)
        for metric in old_env_metrics:
            metric_value = cache.get(metric, -1)
            self.assertEqual(metric_value, -1)


class MiddlewareTest(LiveServerTestCase):
    @override_settings(URL_METRIC_URL_PATTERNS={r"200:GET:\/admin.*": "AdminPageView",
                                                r"200:PUT:\/asd/asd/.*": "Change ASD",},
                       URL_METRIC_EXPORT_ENGINE="dummy",)
    def test_basic_middleware(self):
        exports.DummyExporter.clear_metrics()
        self.client.put("/asd/asd/")
        self.assertEqual(exports.DummyExporter.instance.metrics.get("Change ASD", None), 1)

    @override_settings(URL_METRIC_URL_PATTERNS={r"200:GET:\/admin.*": "AdminPageView",
                                                r"200:PUT:\/asd/asd/.*": "Change ASD",
                                                r"200:PUT:\/asd/asd/das": "Change ASD",},
                       URL_METRIC_EXPORT_ENGINE="dummy",)
    def test_multiple_matches(self):
        exports.DummyExporter.clear_metrics()
        self.client.put("/asd/asd/das")
        self.assertEqual(exports.DummyExporter.instance.metrics.get("Change ASD", None), 1)

    @override_settings(MIDDLEWARE_CLASSES=['url_metric.middleware.RequestTimerMiddleware'],
                       URL_METRIC_EXPORT_ENGINE="dummy",)
    def test_request_timer(self):
        exports.DummyExporter.clear_metrics()
        self.client.put("/asd/asd/das")
        self.assertIsNotNone(exports.DummyExporter.instance.metrics.get("Request.Duration", None))
