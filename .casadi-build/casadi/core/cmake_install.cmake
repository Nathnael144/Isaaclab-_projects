# Install script for directory: /home/nathan/IsaacLab/.casadi-src/casadi/core

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/nathan/IsaacLab/.casadi-install")
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
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/casadi-cli" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/casadi-cli")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/casadi-cli"
         RPATH "/home/nathan/IsaacLab/.casadi-install/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE EXECUTABLE FILES "/home/nathan/IsaacLab/.casadi-build/bin/casadi-cli")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/casadi-cli" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/casadi-cli")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/casadi-cli"
         OLD_RPATH "/home/nathan/IsaacLab/.casadi-build/lib::"
         NEW_RPATH "/home/nathan/IsaacLab/.casadi-install/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/casadi-cli")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcasadi.so.3.7" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcasadi.so.3.7")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcasadi.so.3.7"
         RPATH "/home/nathan/IsaacLab/.casadi-install/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/nathan/IsaacLab/.casadi-build/lib/libcasadi.so.3.7")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcasadi.so.3.7" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcasadi.so.3.7")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcasadi.so.3.7"
         OLD_RPATH ":::::::::::::::::::::::::::::::::::::::::"
         NEW_RPATH "/home/nathan/IsaacLab/.casadi-install/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libcasadi.so.3.7")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/nathan/IsaacLab/.casadi-build/lib/libcasadi.so")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/home/nathan/IsaacLab/.casadi-install/include/casadi/core/casadi_limits.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/casadi_types.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/casadi_common.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/casadi_logger.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/casadi_interrupt.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/exception.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/casadi_enum.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/calculus.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/global_options.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/casadi_meta.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/printable.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/shared_object.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/generic_type.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/options.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/casadi_misc.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/timing.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/polynomial.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/generic_expression.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/generic_matrix.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/generic_shared.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/generic_shared_internal.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/generic_shared_impl.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/matrix_fwd.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/matrix_decl.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/sx_fwd.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/sx.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/dm_fwd.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/dm.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/im_fwd.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/im.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/sparsity_interface.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/sparsity.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/slice.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/submatrix.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/nonzeros.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/sx_elem.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/sx.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/mx.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/function.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/callback.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/external.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/linsol.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/rootfinder.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/integrator.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/nlpsol.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/conic.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/dple.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/interpolant.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/expm.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/code_generator.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/importer.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/blazing_spline.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/integration_tools.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/nlp_tools.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/nlp_builder.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/xml_node.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/xml_file.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/dae_builder.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/optistack.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/serializer.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/serializing_stream.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/fmu.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/tools.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/resource.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/archiver.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/filesystem.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/core.hpp;/home/nathan/IsaacLab/.casadi-install/include/casadi/core/casadi_export.h")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/home/nathan/IsaacLab/.casadi-install/include/casadi/core" TYPE FILE FILES
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/casadi_limits.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/casadi_types.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/casadi_common.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/casadi_logger.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/casadi_interrupt.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/exception.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/casadi_enum.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/calculus.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/global_options.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/casadi_meta.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/printable.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/shared_object.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/generic_type.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/options.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/casadi_misc.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/timing.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/polynomial.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/generic_expression.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/generic_matrix.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/generic_shared.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/generic_shared_internal.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/generic_shared_impl.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/matrix_fwd.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/matrix_decl.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/sx_fwd.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/sx.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/dm_fwd.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/dm.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/im_fwd.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/im.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/sparsity_interface.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/sparsity.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/slice.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/submatrix.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/nonzeros.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/sx_elem.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/sx.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/mx.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/function.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/callback.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/external.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/linsol.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/rootfinder.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/integrator.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/nlpsol.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/conic.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/dple.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/interpolant.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/expm.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/code_generator.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/importer.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/blazing_spline.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/integration_tools.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/nlp_tools.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/nlp_builder.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/xml_node.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/xml_file.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/dae_builder.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/optistack.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/serializer.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/serializing_stream.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/fmu.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/tools.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/resource.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/archiver.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/filesystem.hpp"
    "/home/nathan/IsaacLab/.casadi-src/casadi/core/core.hpp"
    "/home/nathan/IsaacLab/.casadi-build/casadi/core/casadi_export.h"
    )
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/home/nathan/IsaacLab/.casadi-build/casadi/core/runtime/cmake_install.cmake")

endif()

