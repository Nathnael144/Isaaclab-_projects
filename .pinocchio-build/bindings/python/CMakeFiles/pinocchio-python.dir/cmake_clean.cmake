file(REMOVE_RECURSE
  "pinocchio/__init__.pyc"
  "pinocchio/casadi/__init__.pyc"
  "pinocchio/deprecated.pyc"
  "pinocchio/deprecation.pyc"
  "pinocchio/derivative/dcrba.pyc"
  "pinocchio/derivative/lambdas.pyc"
  "pinocchio/derivative/xm.pyc"
  "pinocchio/explog.pyc"
  "pinocchio/robot_wrapper.pyc"
  "pinocchio/romeo_wrapper.pyc"
  "pinocchio/shortcuts.pyc"
  "pinocchio/utils.pyc"
  "pinocchio/visualize/__init__.pyc"
  "pinocchio/visualize/base_visualizer.pyc"
  "pinocchio/visualize/gepetto_visualizer.pyc"
  "pinocchio/visualize/meshcat_visualizer.pyc"
  "pinocchio/visualize/panda3d_visualizer.pyc"
  "pinocchio/visualize/rviz_visualizer.pyc"
  "pinocchio/visualize/viser_visualizer.pyc"
  "pinocchio/visualize/visualizers.pyc"
  "pinocchio/windows_dll_manager.pyc"
)

# Per-language clean rules from dependency scanning.
foreach(lang )
  include(CMakeFiles/pinocchio-python.dir/cmake_clean_${lang}.cmake OPTIONAL)
endforeach()
