#!/usr/bin/env python

from distutils.core import setup

setup(name='url_metric',
      version='1.0',
      description='Django url metric app',
      author='Margus Laak',
      author_email='margus.laak@redfunction.ee',
      url='https://bitbucket.org/redfunction/django-url-metric',
      packages=['url_metric', 'url_metric.management.commands'],
     )