#-----------------------------------------------------------------------------
set(MODULE_NAME SliceStat)

# Find source files for the module
set(MODULE_SRCS
  ${MODULE_NAME}.py
  )

# Slicer-specific logic to package the Python module
if(Slicer_SOURCE_DIR)
  set(MODULE_PYTHON_SRCS ${MODULE_SRCS})

  slicer_package_module(${MODULE_NAME}
    PACKAGE_PYTHON_SCRIPTS
    SCRIPTS ${MODULE_PYTHON_SRCS}
    INSTALL_SCRIPT_DIR ${Slicer_INSTALL_QTLOADABLEMODULES_DIR}
    COMPONENT ${Slicer_DEFAULT_CLI_INSTALL_COMPONENT}
    )
endif()
