cmake_minimum_required(VERSION 3.15)
project(assimp-python-binding)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 设置RPATH，确保动态库能被找到
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
if(APPLE)
    set(CMAKE_INSTALL_RPATH "@loader_path")
else()
    set(CMAKE_INSTALL_RPATH "$ORIGIN")
endif()

if(UNIX AND NOT APPLE)
    set(ASSIMP_BUILD_ZLIB ON CACHE BOOL "Build ZLIB on Linux" FORCE)
endif()

add_subdirectory(assimp)

# 查找pybind11
find_package(pybind11 REQUIRED)

# 创建Python扩展模块
pybind11_add_module(assimp_export_core
    src/assimp_export.cpp
)

# 链接assimp库
target_link_libraries(assimp_export_core PRIVATE assimp)

# 设置包含目录
target_include_directories(assimp_export_core PRIVATE
    assimp/include
    ${CMAKE_CURRENT_BINARY_DIR}/assimp/include
)

# 编译定义
target_compile_definitions(assimp_export_core PRIVATE VERSION_INFO="${PROJECT_VERSION}")

# 安装扩展模块
install(TARGETS assimp_export_core
    COMPONENT python
    LIBRARY DESTINATION .
    RUNTIME DESTINATION .
)

# 安装 Python 包资源到包根
install(FILES
    src/assimp_python_binding/__init__.py
    src/assimp_python_binding/__init__.pyi
    src/assimp_python_binding/py.typed
    COMPONENT python
    DESTINATION .
)

# 如果使用动态库，需要安装动态库文件
if(BUILD_SHARED_LIBS)
    # 获取assimp动态库路径
    get_target_property(ASSIMP_LOCATION assimp LOCATION)
    install(FILES $<TARGET_FILE:assimp>
        COMPONENT python
        DESTINATION assimp_python_binding
    )
endif()
