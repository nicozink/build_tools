import os
from pathlib import Path
import py_util
import subprocess

def get_emsdk():
    if py_util.is_windows():
        return "emsdk.bat"
    else:
        return "./emsdk"

def get_mingw_root():
    return Path("emsdk") / "mingw" / "7.1.0_64bit" / "bin"

def get_node_js():
    paths = (Path("emsdk") / "node").iterdir()

    for path in paths:
        if (Path(path).is_dir()):
            return Path(path) / "bin" / "node"

def setup():
    if os.path.exists("emsdk"):
        return

    cwd = os.getcwd()

    subprocess.call(["git", "clone", "https://github.com/emscripten-core/emsdk.git"])

    os.chdir("emsdk")

    emsdk_version = "1.39.18"

    subprocess.call([get_emsdk(), "install", emsdk_version])
    subprocess.call([get_emsdk(), "activate", emsdk_version])

    emsdk_version = "mingw-7.1.0-64bit"

    subprocess.call([get_emsdk(), "install", emsdk_version])
    subprocess.call([get_emsdk(), "activate", emsdk_version])

    os.chdir(cwd)
