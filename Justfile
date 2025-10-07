build-locally:
    WORKSPACE_PREFIX="local_" bin/build-locally.bash

build-in-docker:
    WORKSPACE_PREFIX="docker_" bin/build-locally.bash

check:
    ruff format --exit-non-zero-on-format
    ruff check --fix
    ./bin/run-cpp-linters.bash

generate-ros-dep-txt:
    @echo "Generating rosdep dependency list..."
    @temp_file="rosdep-deps.txt.tmp" && \
    docker run --rm -v "$PWD/src:/src" ros:jazzy bash -c "\
        rosdep update >/dev/null 2>&1 && \
        rosdep keys --from-path /src | xargs rosdep resolve | grep -v '^#' | grep -v 'ERROR' | sort" > $$temp_file && \
    if ! cmp -s $$temp_file rosdep-deps.txt; then \
        mv $$temp_file rosdep-deps.txt && echo "Updated rosdep-deps.txt"; \
    else \
        rm $$temp_file && echo "No changes to rosdep-deps.txt"; \
    fi

setup-conan:
    conan profile detect --force
    conan remote update conancenter --url="https://center2.conan.io"

docker-up-example: generate-ros-dep-txt
    docker compose -f docker/docker-compose-example.yml up --build

docker-up-telemetry:
    PROJECT_ROOT="{{invocation_directory()}}" docker compose -f telemetry_services/telemetry/signoz/docker/docker-compose.yaml up -d

add-ros-python-package package path="src":
    @echo 'Adding a new python package {{ package }} in {{ path }}...'
    ros2 pkg create --destination-directory {{ path }} --build-type ament_python {{ package }}
    rm -rf {{ path }}/{{ package }}/test # default tests are garbage
    rm {{ path }}/{{ package }}/setup.py
    cp bin/templates/ros-setup-py.txt {{ path }}/{{ package }}/setup.py
    PROJECT_NAME={{ package }} envsubst < bin/templates/ros-pyproject-toml.txt > {{ path }}/{{ package }}/pyproject.toml

add-ros-cpp-package package type="exe" path="src":
    @echo 'Adding a new C++ package {{ package }} (type={{ type }}) in {{ path }}...'
    ros2 pkg create --destination-directory {{ path }} --build-type ament_cmake {{ package }}
    rm -rf {{ path }}/{{ package }}/src {{ path }}/{{ package }}/include
    mkdir -p {{ path }}/{{ package }}/src {{ path }}/{{ package }}/include/{{ package }}
    sed 's/__PROJECT_NAME__/{{ package }}/g' bin/templates/ros-cpp-package.xml > {{ path }}/{{ package }}/package.xml
    cp bin/templates/ros-cpp-conanfile.txt {{ path }}/{{ package }}/conanfile.txt
    if [ "{{ type }}" = "exe" ]; then \
      sed 's/__PROJECT_NAME__/{{ package }}/g' bin/templates/ros-cpp-exe-CMakeLists.txt > {{ path }}/{{ package }}/CMakeLists.txt; \
      sed 's/__PROJECT_NAME__/{{ package }}/g' bin/templates/ros-cpp-main.cpp > {{ path }}/{{ package }}/src/main.cpp; \
    else \
      sed 's/__PROJECT_NAME__/{{ package }}/g' bin/templates/ros-cpp-lib-CMakeLists.txt > {{ path }}/{{ package }}/CMakeLists.txt; \
      sed 's/__PROJECT_NAME__/{{ package }}/g' bin/templates/ros-cpp-lib.hpp > {{ path }}/{{ package }}/include/{{ package }}/{{ package }}.hpp; \
      sed 's/__PROJECT_NAME__/{{ package }}/g' bin/templates/ros-cpp-lib.cpp > {{ path }}/{{ package }}/src/{{ package }}.cpp; \
    fi
