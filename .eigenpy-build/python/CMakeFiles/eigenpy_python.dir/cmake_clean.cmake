file(REMOVE_RECURSE
  "eigenpy/__init__.pyc"
  "eigenpy/windows_dll_manager.pyc"
)

# Per-language clean rules from dependency scanning.
foreach(lang )
  include(CMakeFiles/eigenpy_python.dir/cmake_clean_${lang}.cmake OPTIONAL)
endforeach()
