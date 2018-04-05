import os

__revision__ = "$Id: //TestCenter/4.81_rel/common/tools/python/2.7.14/linux_64/lib/python2.7/distutils/debug.py#1 $"

# If DISTUTILS_DEBUG is anything other than the empty string, we run in
# debug mode.
DEBUG = os.environ.get('DISTUTILS_DEBUG')
