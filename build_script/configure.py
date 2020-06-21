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

    vcpkg_root = project_root / "vcpkg"

    if args.platform == "emscripten":
        setup_emscripten.setup()

    if vcpkg_root.is_file():
        vcpkg = vcpkg_root / get_vcpkg()

        if not vcpkg.is_dir():
            subprocess.call([vcpkg_root / get_bootstrap_vcpkg()])

        if args.platform == "native":
            vcpkg_triplet = ""
        else:
            os.environ["EMSDK"] = os.path.abspath("emsdk")

            vcpkg_triplet = ":wasm32-emscripten"
        
        subprocess.call([vcpkg, "install", "boost-signals2" + vcpkg_triplet])
        subprocess.call([vcpkg, "install", "boost-system" + vcpkg_triplet])

    if args.platform == "native":
        subprocess.call(["cmake", project_root])
    else:
        if py_util.is_windows():
            subprocess.call([get_emcmake(), "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten", "-G", "NMake Makefiles"])
        else:
            subprocess.call([get_emcmake(), "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten"])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--platform", choices=["native", "emscripten"], default="native", help='The platform')

    main(parser.parse_args())
