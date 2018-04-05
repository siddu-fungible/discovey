'''
Initialize the path used by the unit test framework
'''
import os
import sys
stak_path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                          '..', 'STAKCommands'))
if stak_path not in sys.path:
    sys.path.append(stak_path)
