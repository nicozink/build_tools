import platform
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

def run_command(args, verbose = True):
    if verbose:
        print(*args)

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    output = []
    while(True):
        retcode = p.poll()
        line = p.stdout.readline()
        if line:
            if verbose:
                print(line.decode().strip())

            output.append(line.decode().strip())

        if retcode is not None:
            if retcode != 0:
                print("Failed to run command: {}".format(retcode))

                if not verbose:
                    print(*args)

                    for line in output:
                        print(line)

                raise Exception("Failed to run the command: {}".format(retcode))
            
            return
