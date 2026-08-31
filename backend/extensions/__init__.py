from .exception_handler import add_exception_handlers
from .smtp import add_smtp


def register_extensions(app):
    # Add new extensions imports below.
    add_exception_handlers(app)
    add_smtp(app)
