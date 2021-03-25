
def getVar(name, var):
    import os
    if os.environ.get(name) != None:
        var = os.environ.get(name)
        print(f"Set environment variable {name} = {var}")
    return var

def getConsoleArguments():
    import sys
    import argparse
    # источник видеопотока, номер подключённой к системе камеры или ссылка на удалённую
    # example:
    cameraSource = 0 # работает, локальная камера
    # cameraSource = 'http://homecam:15243@192.168.43.1:8080/video' # работает, ip webcam, локальная сеть
    # cameraSource = "rtsp://op1:Qw123456@109.194.108.56:1554/ISAPI/Streaming/Channels/101" # первая камера: парковка
    # cameraSource = "rtsp://op1:Qw123456@109.194.108.56:2554/ISAPI/Streaming/Channels/101" # вторая камера: офис

    # идентификатор текущего ПО, нужен для сетевого взаимодействия
    idSource = 0

    # адрес назначения, для отправления найденных лиц
    urlDist = "http://127.0.0.1:8000/hook/"
    # urlDist = "https://enhod9mv9wlxpy8.m.pipedream.net" # мой адрес
    # urlDist = "https://enazur7xr2301az.m.pipedream.net" # адрес Романа


    # лица, занимающие меньше X% по среднему арифметическому отношений ширины и высоты к экрану отсеиваются
    kMinFace = 0.01

    # максимальное расстояние между центрами лиц, при котором они считаются одним. Измеряется в долях по отношению к наибольшей стороне прямоугольника лица.
    maxDistance = 0.9

    # частота обработки кадров: количество кадров, которые будут пропущены между обрабатываемыми кадрами. Напрямую влияет на производитедбность.
    kadrToProcess = 50

    # количество кадров, в течение которых прежние положения лиц будут храниться в памяти
    maxKadrEmpty = 5

    # количество непринятых кадров до перевода программы в режим простоя/ожидания
    maxInAccessWebcam = 1

    # время простоя между попытками восстановить связь с камерой, в секундах
    cameraTimeOut = 600

    # коэффициенты уменьшения масштабв входного изображения перед обработкой
    kx = 1
    ky = 1

    cameraSource = getVar("CAMERA_SOURCE", cameraSource)
    idSource = getVar("ID_SOURCE", idSource)
    urlDist = getVar("URL_DIST", urlDist)
    kMinFace = getVar("K_MIN_FACE", kMinFace)
    maxDistance = getVar("MAX_DISTANCE", maxDistance)
    kadrToProcess = getVar("KADR_TO_PROCESS", kadrToProcess)
    maxKadrEmpty = getVar("MAX_KADR_EMPTY", maxKadrEmpty)
    maxInAccessWebcam = getVar("MAX_INACCESS_WEBCAM", maxInAccessWebcam)
    cameraTimeOut = getVar("CAMERA_TIMEOUT", cameraTimeOut)
    kx = getVar("K_X", kx)
    ky = getVar("K_Y", ky)

    parser = argparse.ArgumentParser()
    parser.add_argument('-wc', '--webcam', default=cameraSource)
    parser.add_argument('-id', '--idSource', default=idSource)
    parser.add_argument('-ud', '--urlDist', default=urlDist)
    parser.add_argument('-kf', '--kMinFace', default=kMinFace)
    parser.add_argument('-md', '--maxDistance', default=maxDistance)
    parser.add_argument('-kp', '--kadrToProcess', default=kadrToProcess)
    parser.add_argument('-ke','--maxKadrEmpty', default=maxKadrEmpty)
    parser.add_argument('-iw', '--maxInAccessWebcam', default=maxInAccessWebcam)
    parser.add_argument('-ct', '--cameraTimeOut', default=cameraTimeOut)
    parser.add_argument('-kx', default=kx)
    parser.add_argument('-ky', default=ky)

    namespace = parser.parse_args(sys.argv[1:])

    cameraSource = namespace.webcam
    idSource = int(namespace.idSource)
    urlDist = namespace.urlDist
    kMinFace = float(namespace.kMinFace)
    maxDistance = float(namespace.maxDistance)
    kadrToProcess = int(namespace.kadrToProcess)
    maxKadrEmpty = int(namespace.maxKadrEmpty)
    maxInAccessWebcam = int(namespace.maxInAccessWebcam)
    cameraTimeOut = int(namespace.cameraTimeOut)
    kx = float(namespace.kx)
    ky = float(namespace.ky)

    Sargs = {
        "cameraSource": cameraSource,
        "idSource": idSource,
        "urlDist": urlDist,
        "kMinFace": kMinFace,
        "maxDistance": maxDistance,
        "kadrToProcess": kadrToProcess,
        "maxKadrEmpty": maxKadrEmpty,
        "maxInAccessWebcam": maxInAccessWebcam,
        "cameraTimeOut": cameraTimeOut,
        "kx": kx,
        "ky": ky
    }

    return Sargs
