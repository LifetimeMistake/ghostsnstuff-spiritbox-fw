import platform

def isRaspberryPi():
    system = platform.system()
    cpu = platform.machine()
    return "Linux" in system and "arm" in cpu
    
def isWindows():
    system = platform.system()
    return "Windows" in system