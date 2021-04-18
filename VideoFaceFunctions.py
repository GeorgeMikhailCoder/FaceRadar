from ExtendFunctions import *
import cv2
from face_recognition import face_locations
from requests import post
from os import remove, getcwd
from time import sleep, time
from threading import Thread
from datetime import datetime
import logging.config

## функции обнаружения

def chooseMethod(rgb_small_frame, Sargs):
    # определение координат лиц (прямоугольников)
    # kMinFace = Sargs["kMinFace"]
    # camWidth = Sargs["camWidth"]
    # camHeight = Sargs["camHeight"]

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
    try:
        if type(cameraSource) == str and cameraSource[0:4] == "rtsp": # for rtsp
            video_capture = cv2.VideoCapture(cameraSource, cv2.CAP_FFMPEG)
        else:
            video_capture = cv2.VideoCapture(cameraSource)
    except Exception:
        logger = logging.getLogger("main_logger.VideoFaceFunctions.cameraCapture")
        logger.error("Error while connecting to camera")
        logger.error(Exception.__str__())
    return video_capture

def cameraReconnect(video_capture, Sargs):
    cameraSource = Sargs["cameraSource"]
    maxInAccessWebcam = Sargs["maxInAccessWebcam"]
    cameraTimeOut = Sargs["cameraTimeOut"]
    logger = logging.getLogger("main_logger.VideoFaceFunctions.cameraReconnect")
    logger.error(f"Video doesn't accepted, address of webcam:  {cameraSource}")
    inAccessWebcam = 1
    while True:
        if inAccessWebcam >= maxInAccessWebcam:
            try:
                logger.error(f"Fail to reconnect, next try to reconnect in {cameraTimeOut} seconds")
                video_capture.release()
                sleep(cameraTimeOut)
                now = datetime.now()
                logger.error(f"Try to reconnect, {now.time().__str__()[:8]}")
                video_capture = cameraCapture(Sargs["cameraSource"])
            except Exception:
                logger.error(Exception.__str__())
        else:
            try:
                video_capture.release()
                video_capture = cameraCapture(Sargs["cameraSource"])
            except Exception:
                logger.error(Exception.__str__())

        camWidth = video_capture.get(3)
        if camWidth < 0.1:
            logger.error(f"Video doesn't accepted, address of webcam:  {cameraSource}")
            inAccessWebcam += 1
        else:
            logger.info(f"Connection recieved")
            break
    return video_capture

def upload(image, data, url):
# отправляем картинку по указанному url
    # session = requests.Session()
    # data = arrayImage2json(image)

    name = getcwd()+"/var/tmp/screen"+time().__str__()+".jpg"
    cv2.imwrite(name, image)
    file = open(name, 'rb')

    try:
        r = post(url, data=data, files={"face": file})
    except Exception:
        logger = logging.getLogger("main_logger.VideoFaceFunctions.faceDetected")
        logger.error(f"Error in connection to server, url = {url}")
    finally:
        file.close()
        remove(name)

    # while True:
    #     cv2.imshow("title", image)
    #     if cv2.waitKey(1) & 0xFF == 27:
    #         break
    # session.close()



def faceDetected(frame, newFace, Sargs):
    logger = logging.getLogger("main_logger.VideoFaceFunctions.faceDetected")
    kx = Sargs["kx"]
    ky = Sargs["ky"]
    camWidth = Sargs["camWidth"]
    camHeight = Sargs["camHeight"]
    urlDist = Sargs["urlDist"]
    (top, right, bottom, left) = newFace
    top *= int(1 / ky)
    right *= int(1 / kx)
    bottom *= int(1 / ky)
    left *= int(1 / kx)
    logger.info(f"new face detected {newFace}, face part on the frame = {koefSmall(newFace, kx, ky, camWidth, camHeight)}")
    imageToSend = frame[top:bottom, left:right]
    # cv2.imshow("new face detect!", imageToSend)
    # upload(imageToSend, urlDist)
    dataToSend = {"idSource": Sargs["idSource"]}
    Thread(target=upload, args=(imageToSend, dataToSend, urlDist)).start()

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


## однопоточный рабочий вариант

def oneThreadDetection(video_capture, Sargs):
    logger = logging.getLogger("main_logger.VideoFaceFunctions.oneThreadDetection")
    cameraSource = Sargs["cameraSource"]
    maxInAccessWebcam = Sargs["maxInAccessWebcam"]
    kadrToProcess = Sargs["kadrToProcess"]
    cameraTimeOut = Sargs["cameraTimeOut"]
    last_face_locations = []
    inAccessWebcam = 0
    curKadr = 0
    while True:
        ret, frame = video_capture.read()

        curKadr+=1
        if curKadr%kadrToProcess==0:
            if not ret:
                video_capture = cameraReconnect(video_capture, Sargs)
                continue
            else:
                inAccessWebcam = 0
                frame, cur_face_locations = detect(frame, Sargs)
                tracingFacesSimple(cur_face_locations, last_face_locations, frame, Sargs)
                last_face_locations = makeFaceLocationsElder(cur_face_locations, Sargs["maxKadrEmpty"])

        # cv2.imshow("title", frame)
        # if cv2.waitKey(1) & 0xFF == 27:
        #     break




