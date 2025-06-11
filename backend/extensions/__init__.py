from .exception import add_exception_handlers

def register_extensions(app):
    # Add new extensions imports below.
    add_exception_handlers(app)