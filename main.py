import logging.config
from ConsoleArgParse import getConsoleArguments
from VideoFaceFunctions import *
from os import makedirs, getcwd
from shutil import rmtree
from pathlib import Path
from icecream import ic

if __name__ == "__main__":
# обработка консольных параметров, перезапись констант, если они были переданы
    logging.config.fileConfig('log_conf.conf')
    logger = logging.getLogger("main_logger")
    Sargs = getConsoleArguments()
    logger.info(f":\nstart\n launched with params: \n {Sargs}\nPress Ctrl+C to stop this server in console\n")

    tempDir = getcwd()+"/var/tmp"
    path = Path(tempDir)
    if not path.exists():
        makedirs(tempDir)
        logger.info(f"created path to temp photo: {path}")

    video_capture = cameraCapture(Sargs["cameraSource"])
    camWidth = video_capture.get(3)
    camHeight = video_capture.get(4)
    while camWidth <0.1:
        video_capture = cameraReconnect(video_capture, Sargs)
        camWidth = video_capture.get(3)
        camHeight = video_capture.get(4)
    logger.info(f"camWidth = {camWidth}, camHeigh = {camHeight}")


    Sargs["camWidth"] = camWidth
    Sargs["camHeight"] = camHeight



    oneThreadDetection(video_capture, Sargs) # !!!
    # manyThreadDetection(video_capture, Sargs)

    # закрываем видеопоток и окна
    try:
        print(f"rem tree = {rmtree(tempDir)}")
    except Exception:
        print(Exception.__str__())
        logger.error(Exception.__str__())
    video_capture.release()
    cv2.destroyAllWindows()



