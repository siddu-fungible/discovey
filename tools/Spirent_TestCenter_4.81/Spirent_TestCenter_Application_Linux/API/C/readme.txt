
== Instructions ==

Windows 

    - Add stccppapi.h, stccppapi.cpp, and stccapi.h to your project
    - Edit project link options to link your binary to stcSAL.lib 
      located in this directory
    Running the application - Set both STC_PRIVATE_INSTALL_DIR and PATH environment variables
                              to point to the target Spirent TestCenter installation directory.

Linux (g++)

    - Add stccppapi.h, stccppapi.cpp, and stccapi.h to your project
    - Add link options to link your binary to libstcSAL.so in the 
      Spirent TestCenter installation directory
	Running the application - Set both STC_PRIVATE_INSTALL_DIR and LD_LIBRARY_PATH environment variables
	                          to point to the target Spirent TestCenter installation directory.
							  Optionally, instead of setting LD_LIBRARY_PATH at runtime, you can also
							  use the --rpath option to hard code the Spirent TestCenter installation directory.

To use the Spirent TestCenter C++ API, just include stccppapi.h in your source files



