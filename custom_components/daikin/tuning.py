"""Retry tuning for BRP084 adapters, applied on top of pydaikin.

pydaikin tries a BRP084 request 3 times with a 15s timeout. Some adapters go
silent for a minute or more while staying on Wi-Fi, so keep trying for 100s
instead: 10s per attempt, backing off 2, 4, 8 then 16s after a timeout so a
slow adapter isn't flooded, and 1-2s after other failures. A request's first
retry is logged as a warning, so the log shows how often retries happen.
"""

import logging

from aiohttp import ClientTimeout
from pydaikin.daikin_brp084 import DaikinBRP084
from tenacity import RetryCallState, stop_after_delay, wait_exponential, wait_random

_LOGGER = logging.getLogger(__name__)

HTTP_TIMEOUT = ClientTimeout(total=10)
RETRY_SECONDS = 100

_WAIT_AFTER_TIMEOUT = wait_exponential(multiplier=2, max=16)
_WAIT_AFTER_ERROR = wait_random(min=1, max=2)


def _wait_before_retry(retry_state: RetryCallState) -> float:
    """Back off 2, 4, 8 then 16s after a timeout, and 1-2s after other failures."""
    if isinstance(retry_state.outcome.exception(), TimeoutError):
        return _WAIT_AFTER_TIMEOUT(retry_state)
    return _WAIT_AFTER_ERROR(retry_state)


def _log_retry(retry_state: RetryCallState) -> None:
    """Log a request's first retry as a warning, naming the device.

    Later retries of the same request are logged at debug, so an adapter that
    is down for hours doesn't flood the log.
    """
    device = retry_state.args[0]
    error = retry_state.outcome.exception()
    _LOGGER.log(
        logging.WARNING if retry_state.attempt_number == 1 else logging.DEBUG,
        "Retrying request to %s in %.0fs after %s",
        device.device_ip,
        retry_state.next_action.sleep,
        str(error) or type(error).__name__,
    )


def apply_brp084_tuning() -> None:
    """Swap pydaikin's BRP084 timeout and retry timing for the tuned ones.

    The stop and wait policy change, and retries are logged as above. Which
    errors are retried and reraise stay as pydaikin has them. If pydaikin no
    longer retries with tenacity, leave it alone.
    """
    retry_with = getattr(DaikinBRP084._get_resource, "retry_with", None)  # noqa: SLF001
    if retry_with is None:
        _LOGGER.warning(
            "pydaikin's BRP084 requests no longer use tenacity, so the retry "
            "tuning was not applied"
        )
        return
    DaikinBRP084.HTTP_TIMEOUT = HTTP_TIMEOUT
    DaikinBRP084._get_resource = retry_with(  # noqa: SLF001
        stop=stop_after_delay(RETRY_SECONDS),
        wait=_wait_before_retry,
        before_sleep=_log_retry,
    )
