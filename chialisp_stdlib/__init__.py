try:
    from importlib.resources import files
except ImportError:
    # for py3.8
    from importlib_resources import files

STABLE_INCLUDE_DIRECTORY = files(__package__) / "stable"
NIGHTLY_INCLUDE_DIRECTORY = files(__package__) / "nightly"
