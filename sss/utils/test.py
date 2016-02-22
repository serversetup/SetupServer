"""Testing utilities for Simple Setup Server."""
from ss.cli.main import SSSTestApp
from cement.utils.test import *


class SSSTestCase(CementTestCase):
    app_class = SSSTestApp

    def setUp(self):
        """Override setup actions (for every test)."""
        super(EETestCase, self).setUp()

    def tearDown(self):
        """Override teardown actions (for every test)."""
        super(EETestCase, self).tearDown()
