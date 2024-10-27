import platform

def isRaspberryPi() -> bool:
    system = platform.system()
    cpu = platform.machine()
    return "Linux" in system and "arm" in cpu
    
def isWindows() -> bool:
    system = platform.system()
    return "Windows" in system