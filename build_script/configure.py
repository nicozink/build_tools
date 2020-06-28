import argparse
import os
from pathlib import Path
import platform
import py_util
import setup_emscripten
import subprocess

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

def configure_project(project_root, libraries_root, working_dir, platform):
    project_root = Path(project_root).resolve()

    tools_list = read_tools(libraries_root, project_root)

    for tool in tools_list:
        tool_root = Path("tools") / tool.name
        Path.mkdir(tool_root, parents=True, exist_ok=True)

        cwd = os.getcwd()
        os.chdir(tool_root)
        
        configure_project(tool, libraries_root, working_dir, "native")

        os.chdir(cwd)

        subprocess.call(["cmake", "--install", tool_root])
    
    if platform == "emscripten":
        setup_emscripten.setup()
    
    for library in read_library_list(project_root):
        if not (libraries_root / library).is_dir():
            subprocess.call(["git", "clone", "https://github.com/nicozink/" + library + ".git", libraries_root / library])

    library_folders = read_library_folders(libraries_root, project_root)

    vcpkg_list = list(read_vcpkg_list(libraries_root, project_root))

    if vcpkg_list:
        vcpkg_root = Path("vcpkg")
        vcpkg = vcpkg_root / get_vcpkg()

        if not vcpkg.is_file():
            subprocess.call(["git", "clone", "https://github.com/microsoft/vcpkg.git"])

            cwd = os.getcwd()
            os.chdir(vcpkg_root)
            subprocess.call(["git", "checkout", "ee17a685087a6886e5681e355d36cd784f0dd2c8"])
            os.chdir(cwd)

            subprocess.call([vcpkg_root / get_bootstrap_vcpkg()])

        if platform == "native":
            if py_util.is_windows():
                vcpkg_triplet = ":x64-windows"
            else:
                vcpkg_triplet = ""
        else:
            os.environ["EMSDK"] = os.path.abspath("emsdk")

            vcpkg_triplet = ":wasm32-emscripten"

            if py_util.is_windows():
                subprocess.call([vcpkg, "install", "boost-build:x86-windows"])
        
        for vcpgk_library in vcpkg_list:
            subprocess.call([vcpkg, "install", vcpgk_library + vcpkg_triplet])

    cmake_args = ["-DLIBRARY_FOLDER=" + str(libraries_root), "-DCMAKE_INSTALL_PREFIX=" + str(working_dir)]

    if platform == "native":
        subprocess.call(["cmake", str(project_root)] + (cmake_args))
    else:
        emscripten_args = ["-DNODE_JS=" + os.path.abspath(setup_emscripten.get_node_js())]

        if py_util.is_windows():
            subprocess.call([get_emcmake(), "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten", "-G", "MinGW Makefiles", "-DCMAKE_MAKE_PROGRAM=" + str(setup_emscripten.get_mingw_root() / "mingw32-make.exe")] + cmake_args + emscripten_args)
        else:
            subprocess.call([get_emcmake(), "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten"] + cmake_args + emscripten_args)

    subprocess.call(["cmake", "--build", ".", "--config", "Release"])
    subprocess.call(["ctest", "-VV", "-C", "Release"])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--platform", choices=["native", "emscripten"], default="native", help='The platform')
    parser.add_argument('project_root', type=str, help='The source root directory')

    script_location = Path(os.path.abspath(__file__))
    libraries_root = (script_location / ".." / ".." / "..").resolve()

    working_dir = Path(os.getcwd())

    args = parser.parse_args()
    configure_project(args.project_root, libraries_root, working_dir, args.platform)
