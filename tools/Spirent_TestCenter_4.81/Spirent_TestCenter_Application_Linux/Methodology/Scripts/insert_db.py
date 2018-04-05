import sqlite3


def run(iteration_info, static_string):
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    create_str = 'CREATE TABLE IF NOT EXISTS info (' + \
        'iterationName text, iterationNum text, currentValue text)'
    c.execute(create_str)
    c.execute(
        "insert into info values(?, ?, ?)",
        (iteration_info['iterationName'],
         iteration_info['iterationNum'],
         iteration_info['currentValue']))
    conn.commit()
    conn.close()
