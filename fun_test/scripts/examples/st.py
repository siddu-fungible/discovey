import psutil

def process_exists(process_name):
    result = False
    for proc in psutil.process_iter():
        if result:
            break
        try:
            proc_name = proc.name()
            result = process_name in proc_name
            proc_cmd_line = proc.cmdline()

            if result:
                break
            else:
                for s in proc_cmd_line:
                    result = process_name in s
                    if result:
                        break
        except:
            pass
    return result


if __name__ == "__main__":
    print process_exists(process_name="scheduler.py")