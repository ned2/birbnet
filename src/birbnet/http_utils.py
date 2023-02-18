from . import config
from .exceptions import MisconfiguredException


def create_headers() -> dict:
    """Get HTTP headers required for authenticating to Twitter's API."""
    if config.BEARER_TOKEN is None:
        raise MisconfiguredException("BEARER_TOKEN environment variable not set.")
    return {"Authorization": f"Bearer {config.BEARER_TOKEN}"}


def prepare_params(params: dict) -> dict:
    """Convert dictionary into a prepared params dictionary."""
    preppared_params = {}
    for key, value in params.items():
        if isinstance(value, (list, tuple, set)):
            preppared_params[key] = ",".join(value)
        else:
            preppared_params[key] = value
    return preppared_params
