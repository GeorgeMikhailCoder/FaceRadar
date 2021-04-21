import logging.config
from ConsoleArgParse import getConsoleArguments
from VideoFaceFunctions import *
from os import makedirs, getcwd, path
from shutil import rmtree
from pathlib import Path

if __name__ == "__main__":
    # подключение логгера
    log_file_path = path.join(path.dirname(path.abspath(__file__)), 'log_conf.conf')
    logging.config.fileConfig(log_file_path)
    logger = logging.getLogger("main_logger")

    # обработка консольных параметров, перезапись констант, если они были переданы
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



