import argparse
import os
from pathlib import Path
import platform
import setup_emscripten
import subprocess

def is_darwin():
    if platform.system() == "Darwin":
        return True
    else:
        return False

def is_linux():
    if platform.system() == "Linux":
        return True
    else:
        return False

def is_windows():
    if platform.system() == "Windows":
        return True
    else:
        return False

def get_vcpkg():
    if is_windows():
        return "vcpkg.exe"
    else:
        return "vcpkg"

def get_bootstrap_vcpkg():
    if is_windows():
        return "bootstrap-vcpkg.bat"
    else:
        return "bootstrap-vcpkg.sh"

def main(args):
    print("Build system")
    
    script_location = Path(os.path.abspath(__file__))
    project_root = (script_location / ".." / ".." / "..").resolve()

    vcpkg_root = project_root / "vcpkg"
    vcpkg = vcpkg_root / get_vcpkg()

    if not vcpkg.is_file():
        subprocess.call([vcpkg_root / get_bootstrap_vcpkg()])

    if args.platform == "native":
        vcpkg_triplet = ""
    else:
        setup_emscripten.setup()
        os.environ["EMSDK"] = os.path.abspath("emsdk")

        vcpkg_triplet = ":wasm32-emscripten"
    
    subprocess.call([vcpkg, "install", "boost-signals2" + vcpkg_triplet])
    subprocess.call([vcpkg, "install", "boost-system" + vcpkg_triplet])

    if args.platform == "native":
        subprocess.call(["cmake", project_root])
    else:
        subprocess.call([Path(".") / "emsdk" / "upstream" / "emscripten" / "emcmake", "cmake", project_root, "-DVCPKG_TARGET_TRIPLET=wasm32-emscripten"])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--platform", choices=["native", "emscripten"], default="native", help='The platform')

    main(parser.parse_args())
