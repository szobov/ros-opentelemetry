#!/usr/bin/env bash

# shellcheck disable=SC3040
set -euxo pipefail


function install_python_dependencies() {
    local root_dir

    root_dir="$(realpath -m "$(dirname "$0")/..")"

    local packages_dir="${root_dir}/src"

    echo "Install root dependencies..."
    uv pip install -r "${root_dir}/pyproject.toml"

    find "${packages_dir}" -mindepth 2 -maxdepth 3 -type f -name "pyproject.toml" | while read -r pyproject_file; do
        package_dir="$(dirname "${pyproject_file}")"
        package_name="$(basename "${package_dir}")"
        echo "Installing Python dependencies for ${package_name}..."
        uv pip install -r "${pyproject_file}"
    done
}

function install_cpp_dependencies() {
    local root_dir

    root_dir="$(realpath -m "$(dirname "$0")/..")"

    local packages_dir="${root_dir}/src"

    local workspace_dir="${root_dir}/${WORKSPACE_PREFIX}workspace"
    local workspace_install_dir="${workspace_dir}/install"

    find "${packages_dir}" -mindepth 2 -maxdepth 3 -type f -name "conanfile.txt" | while read -r conanfile_file; do
        package_dir="$(dirname "${conanfile_file}")"
        package_name="$(basename "${package_dir}")"

        echo "Installing C++ dependencies for ${package_name}..."
        conan install "${conanfile_file}" --build=missing \
            -s build_type=Release \
            --output-folder "${workspace_install_dir}"
    done
}

function build_ros_packages() {
    local root_dir
    root_dir="$(realpath "$(dirname "$0")")/.."

    local packages_dir="${root_dir}/src"
    local workspace_dir="${root_dir}/${WORKSPACE_PREFIX}workspace"
    local workspace_src_dir="${workspace_dir}/src"
    local workspace_install_dir="${workspace_dir}/install"
    mkdir -p "${workspace_src_dir}"

    for package_dir in "${packages_dir}"/*; do
        if [ -d "${package_dir}" ]; then
            local package_name
            package_name=$(basename "${package_dir}")

            local symlink_path
            symlink_path="${workspace_src_dir}/${package_name}"
            if [ ! -L "${symlink_path}" ]; then
                ln -s "${package_dir}" "${symlink_path}"
                echo "Created symlink: ${symlink_path} -> ${package_dir}"
            fi
        fi
    done

    install_python_dependencies
    install_cpp_dependencies

    echo "Running colcon build..."
    cd "${workspace_dir}"
    rosdep install --from-paths src --ignore-src -r -y
    # If Conan toolchain exists, pass it to cmake for all packages (harmless if unused)
    CMAKE_TOOLCHAIN_ARG=()
    if [ -f "${workspace_install_dir}/conan_toolchain.cmake" ]; then
        CMAKE_TOOLCHAIN_ARG=("-DCMAKE_TOOLCHAIN_FILE=${workspace_install_dir}/conan_toolchain.cmake" "-DCMAKE_PREFIX_PATH=${workspace_install_dir}")
    fi
    python3 -m colcon build --symlink-install --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Release "${CMAKE_TOOLCHAIN_ARG[@]}"
}

build_ros_packages
