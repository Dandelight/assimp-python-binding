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

# 构建 assimp（作为静态库以避免依赖问题）
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)

# 关闭不必要的功能
set(ASSIMP_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(ASSIMP_BUILD_SAMPLES OFF CACHE BOOL "" FORCE)
set(ASSIMP_BUILD_ASSIMP_TOOLS OFF CACHE BOOL "" FORCE)
set(ASSIMP_INSTALL OFF CACHE BOOL "" FORCE)

# 编译 USD 导入器（依赖 tinyusdz）和所有导出器
set(ASSIMP_BUILD_USD_IMPORTER ON CACHE BOOL "" FORCE)
set(ASSIMP_NO_EXPORT OFF CACHE BOOL "" FORCE)

# Assimp 上游没处理掉的 Warning
set(ASSIMP_WARNINGS_AS_ERRORS OFF CACHE BOOL "" FORCE)

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
    DESTINATION assimp_export
)

# 如果使用动态库，需要安装动态库文件
if(BUILD_SHARED_LIBS)
    # 获取assimp动态库路径
    get_target_property(ASSIMP_LOCATION assimp LOCATION)
    install(FILES $<TARGET_FILE:assimp>
        COMPONENT python
        DESTINATION assimp_export
    )
endif()
