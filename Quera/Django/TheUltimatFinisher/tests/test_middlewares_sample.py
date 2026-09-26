import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory, override_settings
from django.urls import ResolverMatch
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User

from forms.middlewares import FormAccessMiddleware

def _attach_session(req):
    sm = SessionMiddleware(lambda r: HttpResponse("ok"))
    sm.process_request(req)
    req.session.save()
    return req

@override_settings(FORM_REQUEST_SLOW_THRESHOLD=0.01, FORM_ACCESS_LOG_FILE="test_form_access.log")
class FormAccessMiddlewareTestSample(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = FormAccessMiddleware(lambda req: HttpResponse())
        self.user = User.objects.create_user(username='tester', password='pass')

    @patch('forms.middlewares.resolve')
    def test_middlewares_1(self, mock_resolve):
        mock_resolve.return_value = ResolverMatch(func=None, args=(), kwargs={'pk': 1}, url_name='form_detail', app_names=[], namespaces=[])
        request = _attach_session(self.factory.get('/form/1/'))
        request.user = self.user
        self.middleware.process_request(request)
        self.assertTrue(hasattr(request, "_form_access_start_time"))
        self.assertIn('form_start_times', request.session)
        self.assertIn('1', request.session['form_start_times'])

    @patch('forms.middlewares.resolve')
    def test_middlewares_2(self, mock_resolve):
        mock_resolve.return_value = ResolverMatch(func=None, args=(), kwargs={}, url_name='form_detail', app_names=[], namespaces=[])
        request = _attach_session(self.factory.get('/form/'))
        self.middleware.process_request(request)
        self.assertNotIn('form_start_times', request.session)

    def test_middlewares_3(self):
        # dict-like session that also supports `.modified` like Django's real session
        class DummySession(dict):
            pass

        request = MagicMock()
        request.session = DummySession({'form_start_times': {'5': 50.0}})
        request.session.modified = False  # initial state

        with patch('time.time', return_value=60.0):
            FormAccessMiddleware._calculate_completion_time('5', request)

        self.assertAlmostEqual(request.session['form_completion_time'], 10.0, places=2)
        self.assertNotIn('5', request.session['form_start_times'])
        self.assertTrue(request.session.modified)
