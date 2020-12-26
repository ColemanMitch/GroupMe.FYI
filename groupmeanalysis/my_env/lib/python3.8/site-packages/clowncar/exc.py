class Error(Exception):
    pass


class BackendError(Error):
    pass


class NoAvailableBackends(BackendError):
    pass
