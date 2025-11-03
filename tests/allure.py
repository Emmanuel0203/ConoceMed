# Local shim for `allure` to allow running tests without installing the real package.
# This file is placed inside `tests/` so `import allure` in test modules will
# import this shim first when the real allure package isn't installed.
from functools import wraps

class _Step:
    """A small object that can be used both as a decorator and as a context manager."""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, f):
        # When used as a decorator: @allure.step(...)
        return f

    def __enter__(self):
        # No-op context manager enter
        return None

    def __exit__(self, exc_type, exc, tb):
        # No special handling of exceptions
        return False


class _AllureShim:
    def step(self, *args, **kwargs):
        return _Step(*args, **kwargs)

    def feature(self, *args, **kwargs):
        def _decorator(f):
            return f
        return _decorator

    def story(self, *args, **kwargs):
        def _decorator(f):
            return f
        return _decorator

    def severity(self, *args, **kwargs):
        def _decorator(f):
            return f
        return _decorator

    # Keep backward compatibility alias
    def step_context(self, *args, **kwargs):
        return _Step(*args, **kwargs)

    # Common constants used by tests
    class severity_level:
        BLOCKER = 'blocker'
        CRITICAL = 'critical'
        NORMAL = 'normal'
        MINOR = 'minor'
        TRIVIAL = 'trivial'


allure = _AllureShim()

# Also expose the decorator functions at module level so `from allure import step`
# and similar imports keep working (they will get the shim functions/objects).
step = _AllureShim().step
feature = _AllureShim().feature
story = _AllureShim().story
severity = _AllureShim().severity
