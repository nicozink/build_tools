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

	target_include_directories(build_tools
		INTERFACE
		${CMAKE_CURRENT_SOURCE_DIR}/build_tools/cpp
	)
endfunction(initialise_build_tools)

initialise_build_tools()