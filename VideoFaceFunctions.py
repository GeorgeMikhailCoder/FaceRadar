from ExtendFunctions import *
import cv2
from face_recognition import face_locations
from dlib import get_frontal_face_detector, cnn_face_detection_model_v1
from requests import post
from os import remove
from time import sleep, time
from threading import Thread, Lock
from queue import Queue
from os import getcwd
from datetime import datetime

def chooseMethod(rgb_small_frame, Sargs):
    # определение координат лиц (прямоугольников)
    kMinFace = Sargs["kMinFace"]
    camWidth = Sargs["camWidth"]
    camHeight = Sargs["camHeight"]

    # подготовка моделей, в другой файл
    # faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    # HOG_face_detect = get_frontal_face_detector()
    # dnnFaceDetector = cnn_face_detection_model_v1("mmod_human_face_detector.dat")


    # через face_recognition
    cur_face_locations = face_locations(rgb_small_frame)

    # через каскады Хаара
    # gray = cv2.cvtColor(rgb_small_frame, cv2.COLOR_RGB2GRAY)
    # cur_face_locations = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(int(kMinFace*camWidth), int(kMinFace*camHeight)), flags=cv2.CASCADE_SCALE_IMAGE)
    # cur_face_locations = [(top, left + width, top + heigh, left) for (left, top, width, heigh) in cur_face_locations]

    # через HOG
    # gray = cv2.cvtColor(rgb_small_frame, cv2.COLOR_RGB2GRAY)
    # cur_face_locations = HOG_face_detect(gray, 1)
    # cur_face_locations = [(face.top(), face.right(), face.bottom(), face.left()) for face in cur_face_locations]

    # через нейросеть dlib очень медленно
    # gray = cv2.cvtColor(rgb_small_frame, cv2.COLOR_RGB2GRAY)
    # cur_face_locations = dnnFaceDetector(gray, 1)
    # cur_face_locations = [(face.rect.top(), face.rect.right(), face.rect.bottom(), face.rect.left())  for face in cur_face_locations]
    return cur_face_locations

def cameraCapture(cameraSource):
    if type(cameraSource) == str and cameraSource[0:4] == "rtsp": # for rtsp
        video_capture = cv2.VideoCapture(cameraSource, cv2.CAP_FFMPEG)
    else:
        video_capture = cv2.VideoCapture(cameraSource)
    return video_capture

def upload(image, url):
# отправляем картинку по указанному url
    # session = requests.Session()
    # data = arrayImage2json(image)
    name = getcwd()+"/var/tmp/screen"+time().__str__()+".jpg"
    cv2.imwrite(name, image)
    file = open(name, 'rb')
    try:
        r = post(url, files={name: file})
    except Exception:
        print("Error in connection to server")
    finally:
        file.close()
        remove(name)
    # session.close()

def faceDetected(frame, newFace, Sargs):
    kx = Sargs["kx"]
    ky = Sargs["ky"]
    camWidth = Sargs["camWidth"]
    camHeight = Sargs["camHeight"]
    urlDist = Sargs["urlDist"]
    print(f"new face detect! {newFace}")
    (top, right, bottom, left) = newFace
    top *= int(1 / ky)
    right *= int(1 / kx)
    bottom *= int(1 / ky)
    left *= int(1 / kx)
    print(f"k = {koefSmall(newFace, kx, ky, camWidth, camHeight)}")
    imageToSend = frame[top:bottom, left:right]
    # cv2.imshow("new face detect!", imageToSend)
    # upload(imageToSend, urlDist)
    Thread(target=upload, args=(imageToSend, urlDist)).start()


def tracingFacesSimple(cur_face_locations, last_face_locations, frame, Sargs):
    maxDistance = Sargs["maxDistance"]
    maxKadrEmpty = Sargs["maxKadrEmpty"]
    for newFace in cur_face_locations:
        for oldFace in last_face_locations:
            if differ(oldFace["rect"], newFace["rect"]) < maxDistance:
                # найдено соответствие лица в прошлом
                oldFace["notInCam"] = 0
                break
        else:
            # не найдено ни одного соответствия лица
            faceDetected(frame, newFace["rect"], Sargs)

    for oldFace in last_face_locations:
        if 0 < oldFace["notInCam"] < maxKadrEmpty:
            # сохраняем кадр в памяти
            cur_face_locations.append(oldFace)


    return cur_face_locations

def detect(frame, Sargs):
    kx = Sargs["kx"]
    ky = Sargs["ky"]
    kMinFace = Sargs["kMinFace"]
    camWidth = Sargs["camWidth"]
    camHeight = Sargs["camHeight"]

    # изменение размера, перевод картинки в формат rgb
    cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_small_frame = cv2.resize(frame, (0, 0), fx=kx, fy=ky)
    # frame = rgb_small_frame

    # определили положение лиц
    t0 = time()
    cur_face_locations = chooseMethod(rgb_small_frame, Sargs)
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

def ThreadProcess(frame, QVideoFrames, QTracing, prevProc, Sargs):
    frame, cur_face_locations = detect(frame, Sargs)
    prevProc.join()
    QVideoFrames.put(frame)
    last_face_locations = QTracing.get()
    cur_face_locations = tracingFacesSimple(cur_face_locations, last_face_locations, frame, Sargs)
    cur_face_locations = makeFaceLocationsElder(cur_face_locations, Sargs["maxKadrEmpty"])
    QTracing.put(cur_face_locations)


def multyThreadManager(QCameraFrames, QVideoFrames, Sargs, QflagCont):
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
            prevProc = Thread(target=ThreadProcess, args=(frame, QVideoFrames, QTracing, prevProc, Sargs))
            # st = time()
            prevProc.start()
            # print(f"manager time = {time()-st:.3f}")

def camReader(QCameraFrames, video_capture, Sargs, QflagCont):
    cameraSource = Sargs["cameraSource"]
    maxInAccessWebcam=Sargs["maxInAccessWebcam"]
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

        cv2.imshow("videoPlayer", img)
        if cv2.waitKey(1) & 0xFF == 27:
            break

def manyThreadDetection(video_capture, Sargs):
    QflagCont = Queue()
    QCameraFrames = Queue()
    QVideoFrames = Queue()

    CamReader = Thread(target=camReader, args=(QCameraFrames, video_capture, Sargs, QflagCont))
    MultyThreadManager = Thread(target=multyThreadManager, args=(QCameraFrames, QVideoFrames, Sargs, QflagCont))
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

def oneThreadDetection(video_capture, Sargs):
    cameraSource = Sargs["cameraSource"]
    maxInAccessWebcam = Sargs["maxInAccessWebcam"]
    kadrToProcess = Sargs["kadrToProcess"]
    cameraTimeOut = Sargs["cameraTimeOut"]
    last_face_locations = []
    curKadr = 0
    while True:
        ret, frame = video_capture.read()

        curKadr+=1
        if curKadr%kadrToProcess==0:
            if not ret:
                print("Video doesn't accepted!")
                print(f"Address of webcam:  {cameraSource}")
                if inAccessWebcam >= maxInAccessWebcam:
                    print("fail to reconnect")
                    print(f"next try to reconnect in {cameraTimeOut} seconds")
                    sleep(cameraTimeOut)
                    now = datetime.now()
                    print(f"try to reconnect, {now.time().__str__()[:8]}")
                    continue
                else:
                    inAccessWebcam += 1
                    continue
            else:
                inAccessWebcam = 0
                frame, cur_face_locations = detect(frame, Sargs)
                tracingFacesSimple(cur_face_locations, last_face_locations, frame, Sargs)
                last_face_locations = makeFaceLocationsElder(cur_face_locations, Sargs["maxKadrEmpty"])

        # cv2.imshow("title", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

"""
def threadOfDetect(QFaces, frame, Sargs):
    if QFaces.empty():
        last_face_locations = []
    else:
        last_face_locations = QFaces.get()
    frame, cur_face_locations = detect(frame, Sargs)
    tracingFacesSimple(cur_face_locations, last_face_locations, frame, Sargs)
    last_face_locations = makeFaceLocationsElder(cur_face_locations, Sargs["maxKadrEmpty"])
    QFaces.put(last_face_locations)



def oneThreadDetection2(video_capture, Sargs):
    cameraSource = Sargs["cameraSource"]
    maxInAccessWebcam = Sargs["maxInAccessWebcam"]

    last_face_locations = []
    kadrToProcess = 100
    curKadr = 0
    QFaces = Queue()
    while True:
        ret, frame = video_capture.read()

        curKadr+=1
        if curKadr%kadrToProcess==0:
            if not ret:
                print("Video doesn't accepted!")
                print(f"Address of webcam:  {cameraSource}")
                if maxInAccessWebcam == -1:
                    continue
                if inAccessWebcam >= maxInAccessWebcam:
                    print("fail to reconnect")
                    sleep(cameraTimeOut)
                    now = datetime.now()
                    print(f"try to reconnect, {now.time().__str__()[:8]}")
                    continue
                else:
                    inAccessWebcam += 1
                    continue
            else:
                inAccessWebcam = 0
                Thread(target=threadOfDetect, args=(QFaces, frame, Sargs)).start()
        cv2.imshow("title", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
"""
def justToPlay(video_capture, Sargs):
    QFrames = Queue()
    QflagCont = Queue()
    CamReader = Thread(target=camReader, args=(QFrames, video_capture, Sargs, QflagCont))
    VideoPlayer = Thread(target=videoPlayer, args=(QFrames, QflagCont))
    CamReader.start()
    VideoPlayer.start()

    while True:
        if not VideoPlayer.is_alive() \
                or not CamReader.is_alive():
            QflagCont.put(False)
            QflagCont.put(False)
            break
