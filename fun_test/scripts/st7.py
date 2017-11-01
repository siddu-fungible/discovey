class MyExceptipon(Exception):

    def __init__(self, *args):
        super(MyExceptipon, self).__init__(*args)
        print "Yo"

    pass

try:
    raise MyExceptipon("Abc")
except Exception as ex:
    print str(ex.message)