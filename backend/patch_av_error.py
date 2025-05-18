import av.error

def patched_err_check(value, caller_name="unknown"):
    if value < 0:
        error_buffer = av.error.Error._get_error_string(value)
        try:
            error_str = error_buffer.decode('utf-8', errors='replace')
        except UnicodeDecodeError:
            error_str = error_buffer.decode('latin1', errors='replace')
        raise av.error.FFmpegError(value, error_str, caller_name)
    return value

av.error.err_check = patched_err_check