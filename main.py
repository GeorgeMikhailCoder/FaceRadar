import cv2
from face_recognition import face_locations
from requests import post
import sys
import argparse
from math import sqrt, pow
from pandas import DataFrame
from os import remove
from time import sleep, time
from icecream import ic
from cv2 import CascadeClassifier
from dlib import cnn_face_detection_model_v1
from dlib import get_frontal_face_detector
from threading import Thread, Lock
from queue import Queue
from ExtendFunctions import *


print("start")
# источник видеопотока, номер подключённой к системе камеры или ссылка на удалённую
# example:
# cameraSource = 0 # работает, локальная камера
# cameraSource = 'http://homecam:15243@192.168.43.1:8080/video' # работает, ip webcam, локальная сеть
# cameraSource = "rtsp://op1:Qw123456@109.194.108.56:1554/ISAPI/Streaming/Channels/101" # первая камера: парковка
# cameraSource = "rtsp://op1:Qw123456@109.194.108.56:2554/ISAPI/Streaming/Channels/101" # вторая камера: офис
cameraSource = 0

# адрес назначения, для отправления найденных лиц
urlDist = "http://127.0.0.1:8000"
# urlDist = "https://enhod9mv9wlxpy8.m.pipedream.net" # мой адрес
# urlDist = "https://enazur7xr2301az.m.pipedream.net" # адрес Романа


# лица, занимающие меньше X% по среднему арифметическому отношений ширины и высоты к экрану отсеиваются
kMinFace = 0.01

# количество кадров, в течение которых прежние положения лиц будут храниться в памяти
maxKadrEmpty = 50

# количество непринятых кадров до завершения программы
maxInAccessWebcam = 1

# коэффициенты уменьшения масштабв входного изображения перед обработкой
kx = 1
ky = 1


# максимальное расстояние между центрами лиц, при котором они считаются одним. Измеряется в долях по отношению к наибольшей стороне прямоугольника лица.
maxDistance = 0.9

def upload(image, url):
# отправляем картинку по указанному url
    # session = requests.Session()
    # data = arrayImage2json(image)
    name = "screen"+time().__str__()+".jpg"
    cv2.imwrite(name, image)
    file = open(name, 'rb')
    try:
        r = post(urlDist, files={name: file})
    except Exception:
        print("Error in connection to server")
    finally:
        file.close()
        remove(name)
    # session.close()

def faceDetected(frame, newFace):
    print(f"new face detect! {newFace}")
    (top, right, bottom, left) = newFace
    top *= int(1 / ky)
    right *= int(1 / kx)
    bottom *= int(1 / ky)
    left *= int(1 / kx)
    print(f"k = {koefSmall(newFace, kx, ky, camWidth, camHeight)}")
    imageToSend = frame[top:bottom, left:right]
    cv2.imshow("new face detect!", imageToSend)
    # upload(imageToSend, urlDist)
    Thread(target=upload, args=(imageToSend, urlDist)).start()

def makeFaceLocationsElder(faceLocations):
    for face in faceLocations:
        face["notInCam"] += 1
        if face["notInCam"] > maxKadrEmpty:
            faceLocations.remove(face)
            # удаляет первое вхождение face, одинаковых прямоугольников не бывает
    return faceLocations


def tracingFacesSimple(cur_face_locations, last_face_locations, frame):
    for newFace in cur_face_locations:
        for oldFace in last_face_locations:
            if differ(oldFace["rect"], newFace["rect"]) < maxDistance:
                # найдено соответствие лица в прошлом
                oldFace["notInCam"] = 0
                break
        else:
            # не найдено ни одного соответствия лица
            faceDetected(frame, newFace["rect"])

    for oldFace in last_face_locations:
        if 0 < oldFace["notInCam"] < maxKadrEmpty:
            # сохраняем кадр в памяти
            cur_face_locations.append(oldFace)


    return cur_face_locations

def detect(frame):

    # изменение размера, перевод картинки в формат rgb
    cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_small_frame = cv2.resize(frame, (0, 0), fx=kx, fy=ky)
    # frame = rgb_small_frame

    # определили положение лиц
    t0 = time()
    cur_face_locations = chooseMethod(rgb_small_frame)
    t1 = time()
    # print(f"face rec: {t1 - t0:.3f}")
    # заполнение массивов (для первого запуска)
    if len(cur_face_locations) == 0:
        cur_face_locations = []
        return (frame, cur_face_locations)


    # отрисовка прямоугольников на экран
    # сравнение размера прямоугольника с минимальным
    for face in cur_face_locations:
        if not isTooSmall(face, kMinFace, kx, ky, camWidth, camHeight):
            frame = drawRect1(frame, face, kx, ky)
        else:
            cur_face_locations.remove(face)

    cur_face_locations = face2struct(cur_face_locations)
    return (frame, cur_face_locations)
"""
    # трекинг: поиск совпадений местонахождеий лиц а прошлом кадре
    # если найдено повторение - прекратить поиск
    # если нет ни одного повторения - вырезать и отправить лицо
    cur_face_locations = face2struct(cur_face_locations)
    # cur_face_locations = tracingFacesSimple(cur_face_locations, last_face_locations)

    # текущий кадр становится прошлым
    # устаревание:
    last_face_locations = makeFaceLocationsElder(cur_face_locations)
    Qarg.put((frame, last_face_locations, kadrEmpty))
    return (frame, last_face_locations, kadrEmpty)
"""

def ThreadProcess(frame, QVideoFrames, QTracing, prevProc):
    frame, cur_face_locations = detect(frame)
    prevProc.join()
    QVideoFrames.put(frame)
    last_face_locations = QTracing.get()
    cur_face_locations = tracingFacesSimple(cur_face_locations, last_face_locations, frame)
    cur_face_locations = makeFaceLocationsElder(cur_face_locations)
    QTracing.put(cur_face_locations)


def multyThreadManager(QCameraFrames, QVideoFrames, QflagCont):
    cont = True
    prevProc = Thread()
    prevProc.start()
    QTracing = Queue()
    QTracing.put([])

    while cont:

        if not QflagCont.empty():
            cont = QflagCont.get()
        if not QCameraFrames.empty():
            frame = QCameraFrames.get()
            prevProc = Thread(target=ThreadProcess, args=(frame, QVideoFrames, QTracing, prevProc))
            # st = time()
            prevProc.start()
            # print(f"manager time = {time()-st:.3f}")

def camReader(QCameraFrames, video_capture, maxInAccessWebcam, QflagCont):
    cont = True
    inAccessWebcam = 0
    while cont:
        if not QflagCont.empty():
            cont = QflagCont.get()

        ret, frame = video_capture.read()

        if not ret:
            print("Video doesn't accepted!")
            print(f"Address of webcam:  {cameraSource}")
            if inAccessWebcam >= maxInAccessWebcam:
                break
            else:
                inAccessWebcam += 1
                continue
        else:
            inAccessWebcam = 0
            QCameraFrames.put(frame)

def videoPlayer(QVideoframes, QflagCont):
    cont = True
    while cont:
        if not QflagCont.empty():
            cont = QflagCont.get()
        if not QVideoframes.empty():
            img = QVideoframes.get()
        else:
            continue

        cv2.imshow("title", img)
        if cv2.waitKey(1) & 0xFF == 27:
            break

def manyThreadDetection(video_capture, maxInAccessWebcam):
    QflagCont = Queue()
    QCameraFrames = Queue()
    QVideoFrames = Queue()

    CamReader = Thread(target=camReader, args=(QCameraFrames, video_capture, maxInAccessWebcam, QflagCont))
    MultyThreadManager = Thread(target=multyThreadManager, args=(QCameraFrames, QVideoFrames, QflagCont))
    VideoPlayer = Thread(target=videoPlayer, args=(QVideoFrames, QflagCont))

    VideoPlayer.start()
    MultyThreadManager.start()
    CamReader.start()

    while True:
        if not VideoPlayer.is_alive() \
                or not CamReader.is_alive() \
                or not MultyThreadManager.is_alive():
            QflagCont.put(False)
            QflagCont.put(False)
            QflagCont.put(False)
            break

def oneThreadDetection(video_capture, maxInAccessWebcam):
    last_face_locations = []
    kadrToProcess = 100
    curKadr = 0
    while True:
        ret, frame = video_capture.read()

        curKadr+=1
        if curKadr%kadrToProcess==0:
            if not ret:
                print("Video doesn't accepted!")
                print(f"Address of webcam:  {cameraSource}")
                if inAccessWebcam >= maxInAccessWebcam:
                    break
                else:
                    inAccessWebcam += 1
                    continue
            else:
                inAccessWebcam = 0
                frame, cur_face_locations = detect(frame)
                tracingFacesSimple(cur_face_locations, last_face_locations, frame)
                last_face_locations = makeFaceLocationsElder(cur_face_locations)

        cv2.imshow("title", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break


def justToPlay(video_capture, maxInAccessWebcam):
    QFrames = Queue()
    QflagCont = Queue()
    CamReader = Thread(target=camReader, args=(QFrames, video_capture, maxInAccessWebcam, QflagCont))
    VideoPlayer = Thread(target=videoPlayer, args=(QFrames, QflagCont))
    CamReader.start()
    VideoPlayer.start()

    while True:
        if not VideoPlayer.is_alive() \
                or not CamReader.is_alive():
            QflagCont.put(False)
            QflagCont.put(False)
            break

# обработка консольных параметров, перезапись констант, если они были переданы
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-wc', '--webcam', default=cameraSource)
    parser.add_argument('-dist', '--urlDist', default=urlDist)
    parser.add_argument('-kmin', default=kMinFace)
    parser.add_argument('-maxKadrEmpty', default=maxKadrEmpty)
    parser.add_argument('-kx', default=kx)
    parser.add_argument('-ky', default=ky)
    namespace = parser.parse_args(sys.argv[1:])
    cameraSource = namespace.webcam
    urlDist = namespace.urlDist
    kMinFace = float(namespace.kmin)
    maxKadrEmpty = int(namespace.maxKadrEmpty)
    kx = float(namespace.kx)
    ky = float(namespace.ky)

    if type(cameraSource) == str and cameraSource[0:4] == "rtsp": # for rtsp
        video_capture = cv2.VideoCapture(cameraSource, cv2.CAP_FFMPEG)
    else:
        video_capture = cv2.VideoCapture(cameraSource)

    camWidth = video_capture.get(3)
    camHeight = video_capture.get(4)
    print(f"camWidth = {camWidth}, camHeigh = {camHeight}")

    # manyThreadDetection(video_capture, maxInAccessWebcam)
    oneThreadDetection(video_capture, maxInAccessWebcam)
    # закрываем видеопоток и окна
    video_capture.release()
    cv2.destroyAllWindows()



