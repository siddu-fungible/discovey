from django.test import TestCase, RequestFactory
from django.test import Client
from fun_global import get_datetime_from_epoch_time, get_epoch_time_from_datetime
import datetime
import json
from web.web_global import PRIMARY_SETTINGS_FILE
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()


class DateTimeTestCase(TestCase):
    def setUp(self):
        pass

    def test_datetime(self):
        c = Client()
        date_time = '2018-08-16T17:13:19.311Z'
        epoch_value = 1534439599311
        pattern = "%Y-%m-%dT%H:%M:%S.%fZ"
        response = c.post('/test/da', data=json.dumps({"date": date_time, "epoch": epoch_value}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        datetime_obj = datetime.datetime.strptime(date_time, pattern)
        epoch = get_epoch_time_from_datetime(datetime_obj)
        self.assertEqual(epoch_value, epoch)
        self.assertEqual(datetime_obj, get_datetime_from_epoch_time(epoch_value))


