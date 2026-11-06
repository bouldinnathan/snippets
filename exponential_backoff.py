"""Reusable exponential backoff for synchronous operations; standard library only."""
from dataclasses import dataclass, field
import errno
import threading


TRANSIENT_ERRNOS = frozenset(
    value for name in (
        'EIO', 'ETIMEDOUT', 'ECONNRESET', 'ECONNABORTED', 'ECONNREFUSED',
        'ENOTCONN', 'ENETDOWN', 'ENETRESET', 'ENETUNREACH', 'EHOSTDOWN',
        'EHOSTUNREACH', 'ESTALE', 'EAGAIN', 'EBUSY', 'EINTR', 'EMFILE', 'ENFILE',
    ) if (value := getattr(errno, name, None)) is not None
)
TRANSIENT_WINERRORS = frozenset((53, 59, 64, 121, 1231, 1232, 1236, 1460))


def is_transient(error):
    return (isinstance(error, (TimeoutError, ConnectionError))
            or getattr(error, 'errno', None) in TRANSIENT_ERRNOS
            or getattr(error, 'winerror', None) in TRANSIENT_WINERRORS)


class RetryCancelled(OSError):
    """An operation or waiting retry was cancelled through its stop event."""
    def __init__(self):
        super().__init__(getattr(errno, 'ECANCELED', errno.EINTR), 'Retry cancelled during shutdown')


def _validate_options(retries, delay, max_delay, jitter):
    import math
    if type(retries) is not int or retries < 0:
        raise ValueError('retries must be a nonnegative integer')
    if not math.isfinite(delay) or delay < 0:
        raise ValueError('delay must be finite and nonnegative')
    if not math.isfinite(max_delay) or max_delay < delay:
        raise ValueError('max_delay must be finite and at least delay')
    if not math.isfinite(jitter) or not 0 <= jitter <= 1:
        raise ValueError('jitter must be between 0 and 1')


def report_retry(error, number, delay, label):
    """Default retry observer; pass on_retry=None to disable console output."""
    import sys
    print(f"\nRetry {number}: {label} in {delay:.2f}s "
          f"after {type(error).__name__}: {error}", file=sys.stderr, flush=True)


def exponential_backoff(operation, *, retries=5, delay=1.0, max_delay=30.0,
                        jitter=.2, stop_event=None, retry_if=is_transient,
                        on_retry=report_retry, label='operation'):
    """Call a zero-argument operation, retrying selected errors with backoff.

    retries counts additional attempts, not the initial call. Delays double
    after each failure; jitter adds 0..jitter proportion without exceeding
    max_delay. The default predicate retries temporary filesystem/network
    errors only. Supply retry_if(error) to support other exception types.

    A shared threading.Event cancels pending waits with RetryCancelled; an
    operation already running must return before it can be stopped. Successful
    results and the final original exception are returned/raised unchanged.
    KeyboardInterrupt and SystemExit always propagate. An optional observer is
    called as on_retry(error, retry_number, actual_delay, label).
    """
    import random
    _validate_options(retries, delay, max_delay, jitter)
    stop = stop_event if stop_event is not None else threading.Event()
    pause_base = delay
    for attempt in range(retries + 1):
        if stop.is_set():
            raise RetryCancelled()
        try:
            return operation()
        except Exception as error:
            if isinstance(error, RetryCancelled) or attempt == retries or not retry_if(error):
                raise
            pause = min(max_delay, pause_base * (1 + random.uniform(0, jitter)))
            if on_retry is not None:
                on_retry(error, attempt+1, pause, label)
            if stop.wait(pause):
                raise RetryCancelled() from error
            pause_base = min(max_delay, pause_base * 2)


@dataclass(frozen=True)
class RetryPolicy:
    """Reusable settings and a shared cancellation event for worker threads."""
    retries: int = 5
    delay: float = 1.0
    max_delay: float = 30.0
    jitter: float = .2
    stop: threading.Event = field(default_factory=threading.Event, repr=False, compare=False)

    def __post_init__(self):
        _validate_options(self.retries, self.delay, self.max_delay, self.jitter)

    def run(self, operation, label):
        return exponential_backoff(operation, retries=self.retries, delay=self.delay,
                                   max_delay=self.max_delay, jitter=self.jitter,
                                   stop_event=self.stop, label=label)
