function(initialise_vcpkg)
	if(EXISTS ${CMAKE_SOURCE_DIR}/vcpkg.json)
		message("Found ${CMAKE_SOURCE_DIR}/vcpkg.json")
	endif()

	set(VCPKG_ROOT ${CMAKE_CURRENT_BINARY_DIR}/vcpkg)
	
	if(NOT DEFINED ${CMAKE_TOOLCHAIN_FILE})
		if(NOT EXISTS ${VCPKG_ROOT})
			message("Cloning vcpkg in ${VCPKG_ROOT}")
			execute_process(COMMAND git clone https://github.com/Microsoft/vcpkg.git ${VCPKG_ROOT})
			# If a reproducible build is desired (and potentially old libraries are # ok), uncomment the
			# following line and pin the vcpkg repository to a specific githash.
			# execute_process(COMMAND git checkout 745a0aea597771a580d0b0f4886ea1e3a94dbca6 WORKING_DIRECTORY ${VCPKG_ROOT})
		else()
			# The following command has no effect if the vcpkg repository is in a detached head state.
			message("Auto-updating vcpkg in ${VCPKG_ROOT}")
			execute_process(COMMAND git pull WORKING_DIRECTORY ${VCPKG_ROOT})
		endif()

		if(NOT EXISTS ${VCPKG_ROOT}/README.md)
			message(FATAL_ERROR "***** FATAL ERROR: Could not clone vcpkg *****")
		endif()
	endif()

	if(WIN32)
		set(BOOST_INCLUDEDIR ${VCPKG_ROOT}/installed/x86-windows/include)
		set(VCPKG_EXEC ${VCPKG_ROOT}/vcpkg.exe)
		set(VCPKG_BOOTSTRAP ${VCPKG_ROOT}/bootstrap-vcpkg.bat)
	else()
		set(VCPKG_EXEC ${VCPKG_ROOT}/vcpkg)
		set(VCPKG_BOOTSTRAP ${VCPKG_ROOT}/bootstrap-vcpkg.sh)
	endif()

	if(NOT EXISTS ${VCPKG_EXEC})
		message("Bootstrapping vcpkg in ${VCPKG_ROOT}")
		execute_process(COMMAND ${VCPKG_BOOTSTRAP} WORKING_DIRECTORY ${VCPKG_ROOT})
	endif()

	if(NOT EXISTS ${VCPKG_EXEC})
		message(FATAL_ERROR "***** FATAL ERROR: Could not bootstrap vcpkg *****")
	endif()

	set(CMAKE_TOOLCHAIN_FILE ${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake CACHE STRING "")

	message("Set up vcpkg at ${CMAKE_TOOLCHAIN_FILE}")

endfunction(initialise_vcpkg)
