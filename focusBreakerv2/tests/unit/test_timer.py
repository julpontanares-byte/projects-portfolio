from unittest.mock import Mock, patch
from focusbreaker.core.timer import CountdownTimer, fmt_time

def test_fmt_time():
    assert fmt_time(0) == "00:00"
    assert fmt_time(59) == "00:59"
    assert fmt_time(60) == "01:00"
    assert fmt_time(3599) == "59:59"
    assert fmt_time(3600) == "01:00:00"
    assert fmt_time(7325) == "02:02:05"

@patch("focusbreaker.core.timer.QTimer")
def test_countdown_timer_init(MockQTimer):
    mock_timer_instance = Mock()
    MockQTimer.return_value = mock_timer_instance

    timer = CountdownTimer()
    assert timer.remaining == 0
    assert not timer.is_running
    mock_timer_instance.setInterval.assert_called_with(1000)
    mock_timer_instance.timeout.connect.assert_called_once()

@patch("focusbreaker.core.timer.QTimer")
def test_countdown_timer_start(MockQTimer):
    mock_timer_instance = Mock()
    MockQTimer.return_value = mock_timer_instance

    timer = CountdownTimer()
    timer.start(10)
    
    assert timer.remaining == 10
    assert timer.is_running
    mock_timer_instance.start.assert_called_once()

@patch("focusbreaker.core.timer.QTimer")
def test_countdown_timer_pause_resume(MockQTimer):
    mock_timer_instance = Mock()
    MockQTimer.return_value = mock_timer_instance

    timer = CountdownTimer()
    timer.start(10)
    timer.pause()
    
    assert not timer.is_running
    mock_timer_instance.stop.assert_called_once()
    
    timer.resume()
    assert timer.is_running
    assert mock_timer_instance.start.call_count == 2

@patch("focusbreaker.core.timer.QTimer")
def test_countdown_timer_stop(MockQTimer):
    mock_timer_instance = Mock()
    MockQTimer.return_value = mock_timer_instance

    timer = CountdownTimer()
    timer.start(10)
    timer.stop()
    
    assert timer.remaining == 0
    assert not timer.is_running
    mock_timer_instance.stop.assert_called_once()

@patch("focusbreaker.core.timer.QTimer")
def test_countdown_timer_add_seconds(MockQTimer):
    timer = CountdownTimer()
    timer.start(10)
    timer.add_seconds(5)
    assert timer.remaining == 15

@patch("focusbreaker.core.timer.QTimer")
def test_countdown_timer_tick(MockQTimer):
    timer = CountdownTimer()
    timer.start(2)
    
    # Simulate first tick
    timer._on_tick()
    assert timer.remaining == 1
    assert timer.is_running
    
    # Simulate second tick
    timer._on_tick()
    assert timer.remaining == 0
    assert not timer.is_running