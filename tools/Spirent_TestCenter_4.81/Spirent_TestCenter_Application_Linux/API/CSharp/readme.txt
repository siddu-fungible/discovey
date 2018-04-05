
== Instructions ==

To use the Spirent TestCenter C# API, just include the following source files in your project.
Stc.cs
StcIntCSharp.cs
StcIntCSharpPINVOKE.cs
StringVector.cs

Note: Spirent TestCenter is only supported in 32 bit mode. Make sure that your executable
targets the 32 bit platform, i.e. for Visual Studio set "Platform target" to x86.

To run:
You must set the STC_DIR environment variable to the Spirent TestCenter installation full path.

Linux users ( mono ):
You must also make sure the Spirent TestCenter installation full path is available, via adding it to
the LD_LIBRARY_PATH environment variable or editing the /etc/ld.so.conf and running ldconfig.

