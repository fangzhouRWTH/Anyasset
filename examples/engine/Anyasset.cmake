# Include at configure time. Does not fetch or upgrade anything.
# Call anyasset_resolve(<project-directory> <logical-id> <output-variable>).
find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
function(anyasset_resolve PROJECT_DIR ASSET_ID OUTPUT_VAR)
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -m anyasset path
                --project "${PROJECT_DIR}" "${ASSET_ID}"
        RESULT_VARIABLE _status OUTPUT_VARIABLE _json ERROR_VARIABLE _error
        OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(NOT _status EQUAL 0)
        message(FATAL_ERROR "Anyasset binding unavailable: ${_error}. Run assetctl sync --locked.")
    endif()
    string(JSON _path GET "${_json}" path)
    set(${OUTPUT_VAR} "${_path}" PARENT_SCOPE)
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
        "${PROJECT_DIR}/assets.toml" "${PROJECT_DIR}/assets.lock.json"
        "${PROJECT_DIR}/.anyasset/resolved.json")
endfunction()
