
from ConsoleArgParse import getConsoleArguments
from VideoFaceFunctions import *



if __name__ == "__main__":

# обработка консольных параметров, перезапись констант, если они были переданы

    Sargs = getConsoleArguments()
    print("start")
    print(f" launched with params: \n {Sargs}")
    video_capture = cameraCapture(Sargs["cameraSource"])
    camWidth = video_capture.get(3)
    camHeight = video_capture.get(4)
    # print(f"camWidth = {camWidth}, camHeigh = {camHeight}")


    Sargs["camWidth"] = camWidth
    Sargs["camHeight"] = camHeight



    oneThreadDetection(video_capture, Sargs)
    # manyThreadDetection(video_capture, Sargs)
    # wheelThreadsDetection(video_capture, Sargs)

    # закрываем видеопоток и окна
    video_capture.release()
    cv2.destroyAllWindows()
