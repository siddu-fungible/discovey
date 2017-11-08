import threading, datetime, time

def f(a):
    print('thread {}'.format(a))
    return

if __name__ == '__main__':
    '''
    t1 = threading.Timer(1, f, (5, ))
    t1.setName('t1')
    t2 = threading.Timer(2, f, (6, ))
    t2.setName('t2')
    t1.start()
    t2.start()
    '''
    t1 = datetime.datetime.now()
    time.sleep(2)
    t2 = datetime.datetime.now()

    print (t1-t2).total_seconds()