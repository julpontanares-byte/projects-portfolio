import pytest
from utils.navigation import go_home
from components.admin_utils import format_id, format_name, format_datetime
from datetime import datetime


class MockPage:
    def __init__(self):
        self.session = {'role': None}
        self.last_route = None

    def go(self, route):
        self.last_route = route


def test_go_home_admin():
    page = MockPage()
    page.session = {'role': 'admin'}
    go_home(page)
    assert page.last_route == '/admin'


def test_go_home_pm():
    page = MockPage()
    page.session = {'role': 'pm'}
    go_home(page)
    assert page.last_route == '/pm'


def test_go_home_tenant():
    page = MockPage()
    page.session = {'role': 'tenant'}
    go_home(page)
    assert page.last_route == '/tenant'


def test_go_home_default():
    page = MockPage()
    page.session = {'role': None}
    go_home(page)
    assert page.last_route == '/'


def test_format_id():
    assert format_id('usr', 123) == 'USR00123'
    assert format_id('lst', 5) == 'LST00005'
    assert format_id('test', None) == 'TEST00000'


def test_format_name():
    assert format_name('john doe') == 'John Doe'
    assert format_name('MARY SMITH') == 'Mary Smith'
    assert format_name('') == ''
    assert format_name(None) == ''


def test_format_datetime():
    dt = datetime(2024, 1, 1, 12, 30, 45)
    assert format_datetime(dt) == '2024-01-01 12:30:45'

    iso_str = '2024-01-01T12:30:45.123456'
    assert format_datetime(iso_str) == '2024-01-01 12:30:45'

    assert format_datetime('') == ''
    assert format_datetime(None) == ''