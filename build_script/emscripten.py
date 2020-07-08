import os
from pathlib import Path
import py_util

class emscripten_toolchain:
    def __init__(self, toolchain_root):
        self.toolchain_root = toolchain_root

        self.setup()

    def get_emsdk(self):
        if py_util.is_windows():
            return "emsdk.bat"
        else:
            return "./emsdk"

    def get_mingw_root(self):
        return self.toolchain_root / "emsdk" / "mingw" / "7.1.0_64bit" / "bin"

    def get_node_js(self):
        paths = (self.toolchain_root / "emsdk" / "node").iterdir()

        for path in paths:
            if (Path(path).is_dir()):
                return Path(path) / "bin" / "node"

    def setup(self):
        if (self.toolchain_root / "emsdk").is_dir():
            return

        cwd = os.getcwd()

        py_util.run_command(["git", "clone", "https://github.com/emscripten-core/emsdk.git", self.toolchain_root / "emsdk"])

        os.chdir(self.toolchain_root / "emsdk")

        emsdk_version = "1.39.18"

        py_util.run_command([self.get_emsdk(), "install", emsdk_version])
        py_util.run_command([self.get_emsdk(), "activate", emsdk_version])

        emsdk_version = "mingw-7.1.0-64bit"

        py_util.run_command([self.get_emsdk(), "install", emsdk_version])
        py_util.run_command([self.get_emsdk(), "activate", emsdk_version])

        os.chdir(cwd)
