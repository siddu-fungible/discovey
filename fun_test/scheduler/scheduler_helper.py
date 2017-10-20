CONSOLE_LOG_EXTENSION = ".logs.txt"
HTML_LOG_EXTENSION = ".html"
LOG_DIR_PREFIX = "s_"

def get_flat_file_name(path):
    parts = path.split("/")
    flat = path
    if len(parts) > 2:
        flat = "_".join(parts[-2:])
    return flat.lstrip("/")

def get_flat_console_log_file_name(path):
    return get_flat_file_name(path=path) + CONSOLE_LOG_EXTENSION

def get_flat_html_log_file_name(path):
    return get_flat_file_name(path=path) + HTML_LOG_EXTENSION

if __name__ == "__main__":
    print get_flat_console_log_file_name(path="/clean_sanity.py")
    print get_flat_html_log_file_name(path="/examples/clean_sanity.py")