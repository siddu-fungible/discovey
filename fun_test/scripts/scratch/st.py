try:
    raise Exception("hi")
except:
    print "got exception"
    raise Exception("new")
finally:
    print "Finally"