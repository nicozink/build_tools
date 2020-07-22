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

def get_vcpkg():
    if py_util.is_windows():
        return "vcpkg.exe"
    else:
        return "vcpkg"

def get_bootstrap_vcpkg():
    if py_util.is_windows():
        return "bootstrap-vcpkg.bat"
    else:
        return "bootstrap-vcpkg.sh"

def read_list(folders_list, file_name):
    read_list = []

    for folder in folders_list:
        if (folder / file_name).is_file():
            with open (folder / file_name, "r") as fileHandler:
                for line in fileHandler.read().split('\n'):
                    if line != "":
                        yield line

def read_library_list(project_root):
    return read_list([project_root], "libraries_list.txt")

def read_library_folders(libraries_root, project_root):
    for folder in read_library_list(project_root):
        yield libraries_root / folder

def read_tools(libraries_root, project_root):
    library_folders = read_library_folders(libraries_root, project_root)

    for library_folder in library_folders:
        for tool in read_list([library_folder], "tools_list.txt"):
            yield library_folder / "tools" / tool

    for tool in read_list([project_root], "tools_list.txt"):
        yield project_root / "tools" / tool

def read_vcpkg_list(libraries_root, project_root, platform):
    if platform == "native":
        if py_util.is_windows():
            vcpkg_triplet = ":x64-windows"
        else:
            vcpkg_triplet = ""
    else:
        vcpkg_triplet = ":wasm32-emscripten"

    library_folders = read_library_folders(libraries_root, project_root)

    for item in read_list(list(library_folders) + [project_root], "vcpkg_list.txt"):
        yield item + vcpkg_triplet

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

        self.setup_libraries(project_root, self.libraries_root)
        self.setup_vcpkg(project_root, self.libraries_root, platform)

        tools_list = list(read_tools(self.libraries_root, project_root))

        for tool in tools_list:
            tool_root = Path("tools") / tool.name
            Path.mkdir(tool_root, parents=True, exist_ok=True)

            cwd = os.getcwd()
            os.chdir(tool_root)
            
            print("Configuring " + tool.name)
            self.generate_cmake(tool, "native")

            os.chdir(cwd)

            print("Building " + tool.name)
            self.run_command(["cmake", "--build", tool_root, "--config", self.config])
            self.run_command(["cmake", "--install", tool_root, "--config", self.config])
        
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

        if self.uses_vcpkg:
            cmake_args += ["-DCMAKE_TOOLCHAIN_FILE=" + str(self.vcpkg_root / "scripts" / "buildsystems" / "vcpkg.cmake")]
        
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

    def setup_libraries(self, project_root, libraries_root):
        project_root = Path(project_root).resolve()
        
        for library in read_library_list(project_root):
            if not (libraries_root / library).is_dir():
                print("Cloning " + library)

                if (self.github_token != ""):
                    self.run_command(["git", "clone", "https://nicozink:" + self.github_token + "@github.com/nicozink/" + library + ".git", libraries_root / library])
                else:
                    self.run_command(["git", "clone", "https://github.com/nicozink/" + library + ".git", libraries_root / library])

    def setup_toolchain(self, platform):
        if platform == "emscripten":
            self.emscripten = emscripten.emscripten_toolchain(self.toolchain_root)

    def setup_vcpkg(self, project_root, libraries_root, platform):
        project_root = Path(project_root).resolve()
        
        vcpkg_list = list(read_vcpkg_list(libraries_root, project_root, platform))

        tools_list = list(read_tools(libraries_root, project_root))
        
        for tool_root in tools_list:
            vcpkg_list += list(read_vcpkg_list(libraries_root, tool_root, "native"))

        if vcpkg_list:
            self.uses_vcpkg = True

            vcpkg_list = list(set(vcpkg_list))
            vcpkg_list.sort()

            vcpkg = self.vcpkg_root / get_vcpkg()

            if not vcpkg.is_file():
                print("Install vcpkg")

                self.run_command(["git", "clone", "https://github.com/microsoft/vcpkg.git", self.vcpkg_root])

                cwd = os.getcwd()
                os.chdir(self.vcpkg_root)
                self.run_command(["git", "checkout", "ee17a685087a6886e5681e355d36cd784f0dd2c8"])
                os.chdir(cwd)

                self.run_command([self.vcpkg_root / get_bootstrap_vcpkg()])

            if platform == "emscripten":
                os.environ["EMSDK"] = str(self.toolchain_root / "emsdk")

                if py_util.is_windows():
                    print("Install boost-build:x86-windows")

                    self.run_command([vcpkg, "install", "boost-build:x86-windows"])
            
            for vcpgk_library in vcpkg_list:
                print("Install " + vcpgk_library)
                self.run_command([vcpkg, "install", vcpgk_library])
        else:
            self.uses_vcpkg = False

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
    project_root = Path(args.project_root).resolve()

    cwd = os.getcwd()
    
    if (working_dir == project_root):
        working_dir = working_dir / "build"

    Path.mkdir(working_dir, parents=True, exist_ok=True)
    os.chdir(working_dir)
    
    generator = cmake_generator(args.config, args.github_token, libraries_root, args.verbose)
    generator.configure(project_root, args.platform)

    os.chdir(cwd)
