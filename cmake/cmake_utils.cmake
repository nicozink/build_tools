if (EXISTS ${CMAKE_BINARY_DIR}/vcpkg/scripts/buildsystems/vcpkg.cmake)
	set(CMAKE_TOOLCHAIN_FILE ${CMAKE_BINARY_DIR}/vcpkg/scripts/buildsystems/vcpkg.cmake)
endif()

if (VCPKG_TARGET_TRIPLET MATCHES "wasm32-emscripten")
	set(VCPKG_CHAINLOAD_TOOLCHAIN_FILE ${CMAKE_BINARY_DIR}/emsdk/upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake)
	set(NODE_JS ${CMAKE_BINARY_DIR}/emsdk/node/12.9.1_64bit/bin/node)
endif()

PROJECT(build_tools VERSION 1.0.0)

# Define the operating system types.
set(WINDOWS_ENUM 0)
set(MACOS_ENUM 1)
set(UNIX_ENUM 2)

# Define the compiler types.
set(CLANG_ENUM 3)
set(GCC_ENUM 4)
set(MINGW_ENUM 5)
set(VISUAL_STUDIO_ENUM 6)

# Define the render systems.
set(SDL_ENUM 7)
set(GLX_ENUM 8)

# Define the architecture.
set(X86_ENUM 9)
set(X64_ENUM 10)

# Detect the operating system.
if (WIN32)
	set(OPERATING_SYSTEM ${WINDOWS_ENUM})
elseif (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
	set(OPERATING_SYSTEM ${MACOS_ENUM})
elseif (UNIX)
	set(OPERATING_SYSTEM ${UNIX_ENUM})
else (WIN32)
	message(FATAL_ERROR "An unknown operating system is being used." )
endif (WIN32)

# Detect the compiler.
if (MSVC)
	set(COMPILER ${VISUAL_STUDIO_ENUM})
elseif (MINGW)
	set(COMPILER ${MINGW_ENUM})
elseif (CMAKE_COMPILER_IS_GNUCC)
	set(COMPILER ${GCC_ENUM})
elseif ("${CMAKE_CXX_COMPILER_ID}" MATCHES "Clang")
	set(COMPILER ${CLANG_ENUM})
else (MSVC)
	message(FATAL_ERROR "An unknown compiler is being used." )
endif (MSVC)

function(enable_maximum_warnings library_name)
    if(MSVC)
        target_compile_options(${library_name} PRIVATE /W4 /WX)
    else()
        target_compile_options(${library_name} PRIVATE -Wall -Wextra -pedantic -Werror)
    endif()
endfunction(enable_maximum_warnings)

function(create_executable executable_name folder_name _source_files)
	set( source_files ${_source_files} ${ARGN} )

	add_executable(${executable_name} ${source_files})
	set_target_properties(${executable_name} PROPERTIES FOLDER ${folder_name})
    
    enable_maximum_warnings(${executable_name})

	foreach(_source IN ITEMS ${source_files})
		get_filename_component(_source_path "${_source}" PATH)
		file(RELATIVE_PATH _source_path_rel "${_src_root_path}" "${_source_path}")
		string(REPLACE "/" "\\" _group_path "${_source_path_rel}")
		source_group("${_group_path}" FILES "${_source}")
	endforeach()
endfunction(create_executable)

function(create_dll library_name folder_name _source_files)
	set( source_files ${_source_files} ${ARGN} )

	add_library(${library_name} SHARED ${source_files})
	set_target_properties(${library_name} PROPERTIES FOLDER ${folder_name})

    enable_maximum_warnings(${library_name})

	foreach(_source IN ITEMS ${source_files})
		get_filename_component(_source_path "${_source}" PATH)
		file(RELATIVE_PATH _source_path_rel "${_src_root_path}" "${_source_path}")
		string(REPLACE "/" "\\" _group_path "${_source_path_rel}")
		source_group("${_group_path}" FILES "${_source}")
	endforeach()
endfunction(create_dll)

function(create_library library_name folder_name _source_files)
	set( source_files ${_source_files} ${ARGN} )

	add_library(${library_name} ${source_files})
	set_target_properties(${library_name} PROPERTIES FOLDER ${folder_name})

    enable_maximum_warnings(${library_name})

	set(_src_root_path "${CMAKE_CURRENT_SOURCE_DIR}/")
	
	foreach(_source IN ITEMS ${source_files})
		get_filename_component(_source_path "${_source}" PATH)
		file(RELATIVE_PATH _source_path_rel "${_src_root_path}" "${_source_path}")
		string(REPLACE "/" "\\" _group_path "${_source_path_rel}")
		source_group("${_group_path}" FILES "${_source}")
	endforeach()
endfunction(create_library)

function(create_interface library_name folder_name _source_files)
	set( source_files ${_source_files} ${ARGN} )

	add_library(${library_name} INTERFACE)
	target_sources(${library_name} INTERFACE ${source_files})

	#set_target_properties(${library_name} PROPERTIES FOLDER ${folder_name})

    #enable_maximum_warnings(${library_name})

	set(_src_root_path "${CMAKE_CURRENT_SOURCE_DIR}/")
	
	foreach(_source IN ITEMS ${source_files})
		get_filename_component(_source_path "${_source}" PATH)
		file(RELATIVE_PATH _source_path_rel "${_src_root_path}" "${_source_path}")
		string(REPLACE "/" "\\" _group_path "${_source_path_rel}")
		source_group("${_group_path}" FILES "${_source}")
	endforeach()
endfunction(create_interface)

function(initialise_build_tools)
	set(SRC_INTERFACE
		${CMAKE_CURRENT_SOURCE_DIR}/build_tools/cpp/build_tools/warnings.h)

	create_interface(build_tools library ${SRC_INTERFACE})

	configure_file (
		"${CMAKE_CURRENT_SOURCE_DIR}/build_tools/cpp/build_tools/platforms.h.in"
		"${CMAKE_CURRENT_BINARY_DIR}/build_tools/cpp/build_tools/platforms.h"
	)

	target_include_directories(build_tools
		INTERFACE
		${CMAKE_CURRENT_SOURCE_DIR}/build_tools/cpp
		${CMAKE_CURRENT_BINARY_DIR}/build_tools/cpp
	)
endfunction(initialise_build_tools)

initialise_build_tools()