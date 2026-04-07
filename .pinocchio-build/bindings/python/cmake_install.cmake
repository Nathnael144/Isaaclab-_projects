# Install script for directory: /home/nathan/IsaacLab/.pinocchio-src/bindings/python

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/nathan/IsaacLab/.pinocchio-install")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so.3.9.0" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so.3.9.0")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so.3.9.0"
         RPATH "\$ORIGIN/../../../../lib")
  endif()
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so.3.9.0")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE SHARED_LIBRARY FILES "/home/nathan/IsaacLab/.pinocchio-build/bindings/python/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so.3.9.0")
  if(EXISTS "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so.3.9.0" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so.3.9.0")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so.3.9.0"
         OLD_RPATH "/home/nathan/IsaacLab/.eigenpy-install/lib:/home/nathan/IsaacLab/_isaac_sim/kit/python/lib/python3.11/site-packages/cmeel.prefix/lib:/home/nathan/IsaacLab/.pinocchio-build/src:"
         NEW_RPATH "\$ORIGIN/../../../../lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so.3.9.0")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE SHARED_LIBRARY FILES "/home/nathan/IsaacLab/.pinocchio-build/bindings/python/pinocchio/pinocchio_pywrap_default.cpython-311-aarch64-linux-gnu.so")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/nathan/IsaacLab/.pinocchio-build/bindings/python/CMakeFiles/pinocchio_pywrap_default.dir/install-cxx-module-bmi-Release.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so.3.9.0" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so.3.9.0")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so.3.9.0"
         RPATH "\$ORIGIN/../../../../lib")
  endif()
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so.3.9.0")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE SHARED_LIBRARY FILES "/home/nathan/IsaacLab/.pinocchio-build/bindings/python/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so.3.9.0")
  if(EXISTS "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so.3.9.0" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so.3.9.0")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so.3.9.0"
         OLD_RPATH "/home/nathan/IsaacLab/.eigenpy-install/lib:/home/nathan/IsaacLab/.casadi-install/lib:/home/nathan/IsaacLab/_isaac_sim/kit/python/lib/python3.11/site-packages/cmeel.prefix/lib:/home/nathan/IsaacLab/.pinocchio-build/src:"
         NEW_RPATH "\$ORIGIN/../../../../lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so.3.9.0")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE SHARED_LIBRARY FILES "/home/nathan/IsaacLab/.pinocchio-build/bindings/python/pinocchio/pinocchio_pywrap_casadi.cpython-311-aarch64-linux-gnu.so")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/nathan/IsaacLab/.pinocchio-build/bindings/python/CMakeFiles/pinocchio_pywrap_casadi.dir/install-cxx-module-bmi-Release.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/casadi/__init__.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/casadi" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/casadi/__init__.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/__init__.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/__init__.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/deprecated.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/deprecated.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/deprecation.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/deprecation.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/utils.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/utils.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/robot_wrapper.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/robot_wrapper.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/romeo_wrapper.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/romeo_wrapper.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/explog.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/explog.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/shortcuts.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/shortcuts.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/windows_dll_manager.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/windows_dll_manager.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/derivative/xm.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/derivative" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/derivative/xm.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/derivative/dcrba.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/derivative" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/derivative/dcrba.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/derivative/lambdas.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/derivative" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/derivative/lambdas.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize/__init__.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/visualize/__init__.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize/base_visualizer.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/visualize/base_visualizer.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize/gepetto_visualizer.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/visualize/gepetto_visualizer.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize/meshcat_visualizer.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/visualize/meshcat_visualizer.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize/panda3d_visualizer.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/visualize/panda3d_visualizer.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize/rviz_visualizer.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/visualize/rviz_visualizer.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize/viser_visualizer.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/visualize/viser_visualizer.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize/visualizers.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.pinocchio-install/lib/python3.11/site-packages/pinocchio/visualize" TYPE FILE FILES "/home/nathan/IsaacLab/.pinocchio-src/bindings/python/pinocchio/visualize/visualizers.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/pkgconfig" TYPE FILE PERMISSIONS OWNER_READ GROUP_READ WORLD_READ OWNER_WRITE FILES "/home/nathan/IsaacLab/.pinocchio-build/bindings/python/pinocchiopy.pc")
endif()

