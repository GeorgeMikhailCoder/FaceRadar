import cv2
from face_recognition import face_locations
from requests import post
import sys
import argparse
from math import sqrt, pow
from pandas import DataFrame
from os import remove
from time import sleep
from icecream import ic
from cv2 import CascadeClassifier
from dlib import cnn_face_detection_model_v1
from dlib import get_frontal_face_detector
<<<<<<< Updated upstream

=======
from threading import Thread, Lock
from queue import Queue
from ExtendFunctions import *
>>>>>>> Stashed changes

print("start")
# источник видеопотока, номер подключённой к системе камеры или ссылка на удалённую
# example:
# cameraSource = 0 # работает, локальная камера
# cameraSource = 'http://homecam:15243@192.168.43.1:8080/video' # работает, ip webcam, локальная сеть
# cameraSource = "rtsp://op1:Qw123456@109.194.108.56:1554/ISAPI/Streaming/Channels/101" # первая камера
cameraSource = "rtsp://op1:Qw123456@109.194.108.56:2554/ISAPI/Streaming/Channels/101" # вторая камера
# cameraSource = 0

# адрес назначения, для отправления найденных лиц
# urlDist = "http://127.0.0.1:8000"
# urlDist = "https://enhod9mv9wlxpy8.m.pipedream.net" # мой адрес
urlDist = "https://enazur7xr2301az.m.pipedream.net" # адрес Романа


# лица, занимающие меньше X% по среднему арифметическому отношений ширины и высоты к экрану отсеиваются
kMinFace = 0.01

# количество кадров, в течение которых прежние положения лиц будут храниться в памяти
maxKadrEmpty = 50

# коэффициенты уменьшения масштабв входного изображения перед обработкой
kx = 0.5
ky = 0.5


# максимальное расстояние между центрами лиц, при котором они считаются одним. Измеряется в долях по отношению к наибольшей стороне прямоугольника лица.
maxDistance = 0.9

<<<<<<< Updated upstream
def differ(oldFace, newFace) -> float:
# коэффициент разницы положений лиц, отношение расстояний между центрами к самой длинной стороне
    (top0, right0, bottom0, left0) = oldFace
    (top1, right1, bottom1, left1) = newFace
    amax = min([(abs(bottom0 - top0)),
                (abs(bottom1 - top1)),
                (abs(right0 - left0)),
                (abs(right1 - left1))
                ]) # минимальная сторона прямоугольника (меньшего лица)
    center0 = [top0 + (bottom0 - top0)/2, left0 + (right0 - left0)/2]
    center1 = [top1 + (bottom1 - top1)/2, left1 + (right1 - left1)/2]

    centerDif = sqrt(
        pow(center1[0] - center0[0], 2) +
        pow(center1[1] - center0[1], 2)
    )
    return centerDif/amax

def arrayImage2json(arrayImage):
# перекодируем картинку в формат json
    a = arrayImage
    red = a[:, :, 0]
    gre = a[:, :, 1]
    blu = a[:, :, 2]

    rpd = DataFrame(data=red)
    gpd = DataFrame(data=gre)
    bpd = DataFrame(data=blu)

    rj = rpd.to_json()
    gj = gpd.to_json()
    bj = bpd.to_json()

    data = {
        "red": rj,
        "green": gj,
        "blue": bj
    }
    return data

=======
>>>>>>> Stashed changes
def upload(image, url):
# отправляем картинку по указанному url
    # session = requests.Session()
    # data = arrayImage2json(image)
    name = "screen.jpg"
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
<<<<<<< Updated upstream
    upload(imageToSend, urlDist)

def ltwh2trbl(ltwh):
    (left, top, width, heigh) = ltwh
    return (top, left + width, top + heigh, left)
    # return ltwh

def showImage(title, image):
    img = cv2.resize(image, (640, 480))
    cv2.imshow(title, img)

=======
    # upload(imageToSend, urlDist)
    Thread(target=upload, args=(imageToSend, urlDist)).start()


def tracingFacesSimple(cur_face_locations, last_face_locations):
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

        # устаревание:
        for newFace in cur_face_locations:
            newFace["notInCam"] += 1

def detect(Qarg):
    frame, last_face_locations, kadrEmpty = Qarg

    # изменение размера, перевод картинки в формат rgb
    cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_small_frame = cv2.resize(frame, (0, 0), fx=kx, fy=ky)
    # frame = rgb_small_frame

    # определили положение лиц
    cur_face_locations = chooseMethod(rgb_small_frame)
    # заполнение массивов (для первого запуска)
    if len(cur_face_locations) == 0:
        kadrEmpty += 1
        if kadrEmpty > maxKadrEmpty:
            last_face_locations = []
        return (frame, last_face_locations, kadrEmpty)
    else:
        kadrEmpty = 0

    # отрисовка прямоугольников на экран
    # сравнение размера прямоугольника с минимальным
    for face in cur_face_locations:
        if not isTooSmall(face, kMinFace, kx, ky, camWidth, camHeight):
            frame = drawRect1(frame, face, kx, ky)
        else:
            cur_face_locations.remove(face)

    # трекинг: поиск совпадений местонахождеий лиц а прошлом кадре
    # если найдено повторение - прекратить поиск
    # если нет ни одного повторения - вырезать и отправить лицо
    cur_face_locations = face2struct(cur_face_locations)
    tracingFacesSimple(cur_face_locations, last_face_locations)

    # текущий кадр становится прошлым
    last_face_locations = cur_face_locations
    return (frame, last_face_locations, kadrEmpty)



def tracingToMultiThread(inArgs, res):
    (frameLast, last_face_locations, kadrEmpty1) = inArgs
    (frame, cur_face_locations, kadrEmpty2) = res

    ic(kadrEmpty2,kadrEmpty1)
    if kadrEmpty2 - kadrEmpty1 == 1:
        return
    elif kadrEmpty2 - kadrEmpty1 < 0:
        for newFace in cur_face_locations:
            faceDetected(frame, newFace)
    else: # kadrEmpty2 = kadrEmpty1 = 0
        for newFace in cur_face_locations:
            for oldFace in last_face_locations:
                if differ(oldFace, newFace) < maxDistance:
                    break
            else:
                faceDetected(frame, newFace)

def threadProcess(argList, func, inArgs, prev):
    global countProc
    res = func(inArgs)
    if None != prev:
        prev.join()
    argList.put(res)

start = time()
>>>>>>> Stashed changes
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

last_face_locations = []
cur_face_locations = []

kadrEmpty = 0
frame = None
faceCascade = CascadeClassifier('haarcascade_frontalface_default.xml')
dnnFaceDetector = cnn_face_detection_model_v1("mmod_human_face_detector.dat")
HOG_face_detect = get_frontal_face_detector()

while True:
    if cv2.waitKey(1) & 0xFF == 27:
        break
    ret, frame = video_capture.read()
    if not ret:
        print("Video doesn't accepted!")
        print(f"Address of webcam:  {cameraSource}")
        break
    else:

        #изменение размера, перевод картинки в формат rgb
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        small_frame = cv2.resize(frame, (0, 0), fx=kx, fy=ky)
        rgb_small_frame = small_frame
        # frame = rgb_small_frame
        # определение координат лиц (прямоугольников):

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


        # заполнение массивов (для первого запуска)
        if len(cur_face_locations) == 0:
            kadrEmpty += 1
            if kadrEmpty>maxKadrEmpty:
                last_face_locations = []
                showImage('Video', frame)
            continue
        else:
            kadrEmpty = 0

        # отрисовка прямоугольников на экран
        # сравнение размера прямоугольника с минимальным
        for face in cur_face_locations:
            if not isTooSmall(face):
                frame = drawRect1(frame, face)
            else:
                cur_face_locations.remove(face)

        # трекинг: поиск совпадений местонахождеий лиц а прошлом кадре
        # если найдено повторение - прекратить поиск
        # если нет ни одного повторения - вырезать и отправить лицо
        for newFace in cur_face_locations:
            for oldFace in last_face_locations:
                if differ(oldFace, newFace) < maxDistance:
                    break
            else:
                faceDetected(frame, newFace)

        # текущий кадр становится прошлым, отрисовка окна видео
        last_face_locations = cur_face_locations
        showImage('Video', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break



# закрываем видеопоток и окна
video_capture.release()
cv2.destroyAllWindows()



