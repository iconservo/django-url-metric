from .settings import root

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '\n%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s'
        },

        'simple': {
            'format': '\n%(asctime)s %(levelname)s %(message)s'
        },



    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },

        'librato_file': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': root('django-url-metric/url_metric/logs') + "/librato.log",
            'formatter': 'simple',
        },
    },

    'loggers': {
        'external.access.Librato': {
            'handlers': ['console', 'librato_file'],
            'level': 'DEBUG',
        },
        'external.debug.Librato': {
            'handlers': ['console', 'librato_file'],
            'level': 'DEBUG',
        },
        'external.error.Librato': {
            'handlers': ['console', 'librato_file'],
            'level': 'DEBUG',
        },
    },
}