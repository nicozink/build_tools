import os
import py_util
import subprocess

def get_emsdk():
    if py_util.is_windows():
        return "emsdk.bat"
    else:
        return "./emsdk"

def setup():
    if os.path.exists("emsdk"):
        return

    cwd = os.getcwd()

    subprocess.call(["git", "clone", "https://github.com/emscripten-core/emsdk.git"])

    os.chdir("emsdk")

    version = "1.39.18"

    subprocess.call([get_emsdk(),  "install", version])
    subprocess.call([get_emsdk(), "activate", version])

    os.chdir(cwd)
