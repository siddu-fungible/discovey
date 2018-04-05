"""distutils.command

Package containing implementation of all the standard Distutils
commands."""

__revision__ = "$Id: //TestCenter/4.81_rel/common/tools/python/2.7.14/linux_64/lib/python2.7/distutils/command/__init__.py#1 $"

__all__ = ['build',
           'build_py',
           'build_ext',
           'build_clib',
           'build_scripts',
           'clean',
           'install',
           'install_lib',
           'install_headers',
           'install_scripts',
           'install_data',
           'sdist',
           'register',
           'bdist',
           'bdist_dumb',
           'bdist_rpm',
           'bdist_wininst',
           'upload',
           'check',
           # These two are reserved for future use:
           #'bdist_sdux',
           #'bdist_pkgtool',
           # Note:
           # bdist_packager is not included because it only provides
           # an abstract base class
          ]
