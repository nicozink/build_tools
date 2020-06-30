import argparse
import os
from pathlib import Path
import platform
import py_util
import setup_emscripten

def get_emcmake():
    root_path = Path("emsdk") / "upstream" / "emscripten"

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

def read_vcpkg_list(libraries_root, project_root):
    library_folders = read_library_folders(libraries_root, project_root)

    return read_list(list(library_folders) + [project_root], "vcpkg_list.txt")

class cmake_generator:
    def __init__(self, github_token, verbose):
        self.working_dir = Path(os.getcwd())
        self.github_token = github_token
        self.verbose = verbose

    def configure(self, project_root, libraries_root, platform):
        project_root = Path(project_root).resolve()

        tools_list = list(read_tools(libraries_root, project_root))

        if tools_list:
            print("Setting up tools:")

        for tool in tools_list:
            tool_root = Path("tools") / tool.name
            Path.mkdir(tool_root, parents=True, exist_ok=True)

            cwd = os.getcwd()
            os.chdir(tool_root)
            
            print("Configuring " + tool.name)
            self.configure(tool, libraries_root, "native")

            os.chdir(cwd)

            print("Building " + tool.name)
            self.run_command(["cmake", "--install", tool_root])
        
        if platform == "emscripten":
            setup_emscripten.setup()
        
        for library in read_library_list(project_root):
            if not (libraries_root / library).is_dir():
                print("Cloning " + library)

                if (self.github_token != ""):
                    self.run_command(["git", "clone", "https://nicozink:" + self.github_token + "@github.com/nicozink/" + library + ".git", libraries_root / library])
                else:
                    self.run_command(["git", "clone", "https://github.com/nicozink/" + library + ".git", libraries_root / library])

        library_folders = read_library_folders(libraries_root, project_root)

        vcpkg_list = list(read_vcpkg_list(libraries_root, project_root))

        if vcpkg_list:
            print("Configuring vcpkg")
                
            vcpkg_root = Path("vcpkg")
            vcpkg = vcpkg_root / get_vcpkg()

            if not vcpkg.is_file():
                print("Clone vcpkg")

                self.run_command(["git", "clone", "https://github.com/microsoft/vcpkg.git"])

                cwd = os.getcwd()
                os.chdir(vcpkg_root)
                self.run_command(["git", "checkout", "ee17a685087a6886e5681e355d36cd784f0dd2c8"])
                os.chdir(cwd)

                print("Bootstrap vcpkg")
                self.run_command([vcpkg_root / get_bootstrap_vcpkg()])

            if platform == "native":
                if py_util.is_windows():
                    vcpkg_triplet = ":x64-windows"
                else:
                    vcpkg_triplet = ""
            else:
                os.environ["EMSDK"] = os.path.abspath("emsdk")

                vcpkg_triplet = ":wasm32-emscripten"

                if py_util.is_windows():
                    print("Install boost-build:x86-windows")

                    self.run_command([vcpkg, "install", "boost-build:x86-windows"])
            
            for vcpgk_library in vcpkg_list:
                print("Install " + vcpgk_library + vcpkg_triplet)
                self.run_command([vcpkg, "install", vcpgk_library + vcpkg_triplet])

        cmake_args = ["-DLIBRARY_FOLDER=" + str(libraries_root), "-DCMAKE_INSTALL_PREFIX=" + str(working_dir)]

        print("Running cmake")

        if platform == "native":
            self.run_command(["cmake", str(project_root)] + (cmake_args))
        else:
            emscripten_args = ["-DNODE_JS=" + os.path.abspath(setup_emscripten.get_node_js())]

            if py_util.is_windows():
                self.run_command([get_emcmake(), "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten", "-G", "MinGW Makefiles", "-DCMAKE_MAKE_PROGRAM=" + str(setup_emscripten.get_mingw_root() / "mingw32-make.exe")] + cmake_args + emscripten_args)
            else:
                self.run_commandl([get_emcmake(), "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten"] + cmake_args + emscripten_args)

        print("Building")
        self.run_command(["cmake", "--build", ".", "--config", "Release"])
        
        print("Running tests")
        py_util.run_command(["ctest", "-VV", "-C", "Release"], verbose = True)

    def run_command(self, command):
        py_util.run_command(command, verbose = self.verbose)


if __name__ == '__main__':
    print("Configuring project")

    parser = argparse.ArgumentParser()

    parser.add_argument("--platform", choices=["native", "emscripten"], default="native", help='The platform')
    parser.add_argument("--github_token", default="", help='The github authentication token')
    parser.add_argument("--verbose", action='store_true', help='Enable verbost output')
    parser.add_argument('project_root', type=str, help='The source root directory')

    script_location = Path(os.path.abspath(__file__))
    libraries_root = (script_location / ".." / ".." / "..").resolve()

    working_dir = Path(os.getcwd())

    args = parser.parse_args()

    generator = cmake_generator(args.github_token, args.verbose)
    generator.configure(args.project_root, libraries_root, args.platform)
