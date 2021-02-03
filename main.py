
from ConsoleArgParse import getConsoleArguments
from VideoFaceFunctions import *
from os import makedirs, getcwd
from shutil import rmtree
from pathlib import Path

if __name__ == "__main__":
# обработка консольных параметров, перезапись констант, если они были переданы
    Sargs = getConsoleArguments()
    print("start")
    print(f" launched with params: \n {Sargs}")
    print("Press Ctrl+C to stop this server in console")
    tempDir = getcwd()+"/var/tmp"
    path = Path(tempDir)
    if not path.exists():
        makedirs(tempDir)
    video_capture = cameraCapture(Sargs["cameraSource"])
    camWidth = video_capture.get(3)
    camHeight = video_capture.get(4)
    # print(f"camWidth = {camWidth}, camHeigh = {camHeight}")


    Sargs["camWidth"] = camWidth
    Sargs["camHeight"] = camHeight



    oneThreadDetection(video_capture, Sargs)
    # manyThreadDetection(video_capture, Sargs)
    # закрываем видеопоток и окна
    try:
        print(f"rem tree = {rmtree(tempDir)}")
    except Exception:
        print(Exception.__str__())
    video_capture.release()
    cv2.destroyAllWindows()



