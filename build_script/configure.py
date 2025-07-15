import argparse
import os
from pathlib import Path
import platform
import py_util
import emscripten

def get_emcmake(toolchain_root):
    root_path = toolchain_root / "emsdk" / "upstream" / "emscripten"

    if py_util.is_windows():
        return root_path / "emcmake.bat"
    else:
        return Path(".") / root_path / "emcmake"

class cmake_generator:
    def __init__(self, config, github_token, libraries_root, verbose):
        self.config = config
        self.github_token = github_token
        self.libraries_root = libraries_root
        self.verbose = verbose
        self.working_dir = Path(os.getcwd())
        self.toolchain_root = self.libraries_root / "toolchain" / py_util.get_system_name()
        self.vcpkg_root = self.toolchain_root / "vcpkg"
        
    def configure(self, project_root, platform):
        project_root = Path(project_root).resolve()
 
        self.setup_toolchain(platform)

        self.generate_cmake(project_root, platform)

        print("Building " + project_root.name)
        
        solution_file = self.working_dir / (project_root.name + ".sln")
        if solution_file.is_file():
            self.run_command(["dotnet", "restore", solution_file])
        
        self.run_command(["cmake", "--build", ".", "--config", self.config])
        
        print("Running tests")
        py_util.run_command(["ctest", "-VV", "-C", self.config], verbose = True)

    def generate_cmake(self, project_root, platform):
        cmake_args = ["-DLIBRARY_FOLDER=" + str(self.libraries_root),
            "-DCMAKE_INSTALL_PREFIX=" + str(self.working_dir),
            "-DCMAKE_TOOLCHAIN_FOLDER=" + str(self.toolchain_root),
            "-DCMAKE_BUILD_TYPE=" + self.config]
        
        print("Running cmake")

        if platform == "native":
            self.run_command(["cmake", str(project_root)] + (cmake_args))
        else:
            emscripten_args = ["-DNODE_JS=" + os.path.abspath(self.emscripten.get_node_js())]

            if py_util.is_windows():
                self.run_command([get_emcmake(self.toolchain_root), "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten", "-G", "MinGW Makefiles", "-DCMAKE_MAKE_PROGRAM=" + str(self.emscripten.get_mingw_root() / "mingw32-make.exe")] + cmake_args + emscripten_args)
            else:
                self.run_commandl([get_emcmake(self.toolchain_root), "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten"] + cmake_args + emscripten_args)

    def run_command(self, command):
        py_util.run_command(command, verbose = self.verbose)

    def setup_toolchain(self, platform):
        if platform == "emscripten":
            self.emscripten = emscripten.emscripten_toolchain(self.toolchain_root)

    def setup_vcpkg(self, project_root, libraries_root, platform):
        project_root = Path(project_root).resolve()

if __name__ == '__main__':
    print("Configuring project")

    parser = argparse.ArgumentParser()

    parser.add_argument("--config", choices=["Debug", "Release"], default="Release", help='The config')
    parser.add_argument("--platform", choices=["native", "emscripten"], default="native", help='The platform')
    parser.add_argument("--github_token", default="", help='The github authentication token')
    parser.add_argument("--verbose", action='store_true', help='Enable verbost output')
    parser.add_argument("--working_dir", default=".", help='The working directory')
    parser.add_argument('project_root', type=str, help='The source root directory')

    script_location = Path(os.path.abspath(__file__))
    libraries_root = (script_location / ".." / ".." / "..").resolve()

    args = parser.parse_args()

    working_dir = Path(args.working_dir).resolve()
    project_root = (libraries_root / Path(args.project_root)).resolve()

    cwd = os.getcwd()
    
    if (working_dir == project_root):
        working_dir = working_dir / "build"

    Path.mkdir(working_dir, parents=True, exist_ok=True)
    os.chdir(working_dir)
    
    generator = cmake_generator(args.config, args.github_token, libraries_root, args.verbose)
    generator.configure(project_root, args.platform)

    os.chdir(cwd)
