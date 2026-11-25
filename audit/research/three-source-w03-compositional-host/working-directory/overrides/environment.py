"""Check the seven fixed guest values and the actual working directory."""
EXPECTED_ENVIRONMENT = {
    "HOME": "/tmp",
    "LC_ALL": "C.UTF-8",
    "LEAN_NUM_THREADS": "1",
    "LEAN_PATH": "/objects",
    "PATH": "/stock/bin",
    "PWD": "/src",
    "TMPDIR": "/tmp",
}


def require_environment(observed, working_directory):
    """Accept the complete declared mapping and the fixed working directory."""
    if type(observed) is not dict or set(observed) != set(EXPECTED_ENVIRONMENT):
        raise ValueError("unexpected environment variable names")
    for name, expected in EXPECTED_ENVIRONMENT.items():
        if type(observed[name]) is not str or observed[name] != expected:
            raise ValueError("unexpected value for " + name)
    if type(working_directory) is not str or working_directory != "/src":
        raise ValueError("unexpected working directory")
