def try_bool(value, default=None):
    try:
        return bool(value)
    except ValueError:
        return default