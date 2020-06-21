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

def main(args):
    print("Build system")
    
    script_location = Path(os.path.abspath(__file__))
    project_root = (script_location / ".." / ".." / "..").resolve()

    if args.platform == "emscripten":
        setup_emscripten.setup()

    vcpkg_list = project_root.rglob("vcpkg_list.txt")
    
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

        if args.platform == "native":
            if py_util.is_windows():
                vcpkg_triplet = ":x64-windows"
            else:
                vcpkg_triplet = ""
        else:
            os.environ["EMSDK"] = os.path.abspath("emsdk")

            vcpkg_triplet = ":wasm32-emscripten"

            if py_util.is_windows():
                subprocess.call([vcpkg, "install", "boost-build:x86-windows"])
        
        for vcpgk_file in vcpkg_list:
            with open (vcpgk_file, "r") as fileHandler:
                for line in fileHandler.read().split('\n'):
                    if line != "":
                        subprocess.call([vcpkg, "install", line + vcpkg_triplet])

    if args.platform == "native":
        subprocess.call(["cmake", project_root])
    else:
        if py_util.is_windows():
            subprocess.call([get_emcmake(), "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten", "-G", "MinGW Makefiles", "-DCMAKE_MAKE_PROGRAM=" + str(setup_emscripten.get_mingw_root() / "mingw32-make.exe")])
        else:
            subprocess.call([get_emcmake(), "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten"])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--platform", choices=["native", "emscripten"], default="native", help='The platform')

    main(parser.parse_args())
