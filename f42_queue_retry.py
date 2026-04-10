from f20_core_config import get_settings


def should_retry_error(error_message: str, attempt_count: int) -> bool:
    settings = get_settings()

    if attempt_count >= settings.queue_max_attempts - 1:
        return False

    message = (error_message or "").lower()

    non_retryable_markers = [
        "invalid api key",
        "authentication",
        "permission denied",
        "unsupported",
        "not defined",
        "syntaxerror",
        "validationerror",
        "attribute 'get'",
        "400",
        "401",
        "403",
        "404",
    ]

    transient_markers = [
        "timeout",
        "timed out",
        "connection reset",
        "connection aborted",
        "temporarily unavailable",
        "service unavailable",
        "502",
        "503",
        "504",
    ]

    if any(marker in message for marker in non_retryable_markers):
        return False

    if any(marker in message for marker in transient_markers):
        return attempt_count < 1

    return False