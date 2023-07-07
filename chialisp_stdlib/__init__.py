from importlib.resources import files


STABLE_INCLUDE_DIRECTORY = files(__package__) / "stable"
NIGHTLY_INCLUDE_DIRECTORY = files(__package__) / "nightly"
