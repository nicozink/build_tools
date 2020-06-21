import platform

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
