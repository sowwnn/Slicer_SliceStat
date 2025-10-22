cmake_minimum_required(VERSION 3.5)
project(SliceStat)

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

# This line reads the SliceStat.s4ext file for metadata
slicer_process_extension_description(${CMAKE_CURRENT_SOURCE_DIR}/SliceStat.s4ext)

# This line tells CMake to look inside the "SliceStat" subdirectory for the module
add_subdirectory(SliceStat)
