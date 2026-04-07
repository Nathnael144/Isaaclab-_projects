# CMake generated Testfile for 
# Source directory: /home/nathan/IsaacLab/.pinocchio-src/unittest/python/pybind11
# Build directory: /home/nathan/IsaacLab/.pinocchio-build/unittest/python/pybind11
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test([=[test-py-cpp2pybind11]=] "/home/nathan/IsaacLab/_isaac_sim/python.sh" "/home/nathan/IsaacLab/.pinocchio-src/unittest/python/pybind11/test-cpp2pybind11.py")
set_tests_properties([=[test-py-cpp2pybind11]=] PROPERTIES  ENVIRONMENT "PYTHONPATH=/home/nathan/IsaacLab/.pinocchio-build/bindings/python:/home/nathan/IsaacLab/.pinocchio-build/unittest/python/pybind11:/home/nathan/USD_install/lib/python:/opt/ros/jazzy/lib/python3.12/site-packages:/home/nathan/USD_install/lib/python" _BACKTRACE_TRIPLES "/home/nathan/IsaacLab/.pinocchio-build/_deps/jrl-cmakemodules-src/test.cmake;207;add_test;/home/nathan/IsaacLab/.pinocchio-src/unittest/python/pybind11/CMakeLists.txt;37;add_python_unit_test;/home/nathan/IsaacLab/.pinocchio-src/unittest/python/pybind11/CMakeLists.txt;0;")
