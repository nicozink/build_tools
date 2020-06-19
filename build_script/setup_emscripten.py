import os
import subprocess

def setup():
    if os.path.exists("emsdk"):
        return

    cwd = os.getcwd()

    subprocess.call(["git", "clone", "https://github.com/emscripten-core/emsdk.git"])

    os.chdir("emsdk")

    version = "1.39.18"

    subprocess.call(["./emsdk",  "install", version])
    subprocess.call(["./emsdk", "activate", version])

    os.chdir(cwd)
