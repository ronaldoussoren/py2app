Frequently Asked Questions
==========================

* "Mach-O header may be too large to relocate"

  Py2app will fail with a relocation error when
  it cannot rewrite the load commands in shared
  libraries and binaries copied into the application
  or plugin bundle.

  This error can be avoided by rebuilding binaries
  with enough space in the Mach-O headers, either
  by using the linker flag "-headerpad_max_install_names"
  or by installing shared libraries in a deeply
  nested location (the path for the install root needs
  to be at least 30 characters long).
