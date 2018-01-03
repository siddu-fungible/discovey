def initialize_result(failed=False):
    status = True
    if failed:
        status = False
    return {"status": status, "error_message": "", "message": "", "data": None}
