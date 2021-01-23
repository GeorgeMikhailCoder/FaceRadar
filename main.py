import cv2
from face_recognition import face_locations
from requests import post
import sys
import argparse
from math import sqrt, pow
from pandas import DataFrame

print("start")
# источник видеопотока, номер подключённой к системе камеры или ссылка на удалённую
# example:
# cameraSource = 0 # работает, локальная камера
# cameraSource = 'http://homecam:15243@192.168.43.1:8080/video' # работает, ip webcam, локальная сеть
# cameraSource = "rtsp://op1:Qw123456@109.194.108.56:1554/ISAPI/Streaming/Channels/101"
cameraSource = 0

# адрес назначения, для отправления найденных лиц
urlDist = "http://127.0.0.1:8000"

# лица, занимающие меньше X% по среднему арифметическому отношений ширины и высоты к экрану отсеиваются
kMinFace = 0.1

# количество пустых кадров, в течение которых прежние положения лиц будут храниться в памяти
maxKadrEmpry = 100

# коэффициенты уменьшения масштабв входного изображения перед обработкой
kx = 0.25
ky = 0.25


# максимальное расстояние между центрами лиц, при котором они считаются одним. Измеряется в долях по отношению к наибольшей стороне прямоугольника лица.
maxDistance = 0.9

def differ(oldFace, newFace) -> float:
# коэффициент разницы положений лиц, отношение расстояний между центрами к самой длинной стороне
    (top0, right0, bottom0, left0) = oldFace
    (top1, right1, bottom1, left1) = newFace
    amax = max([(abs(bottom0 - top0)),
                (abs(bottom1 - top1)),
                (abs(right0 - left0)),
                (abs(right1 - left1))
                ]) # максимальная сторона прямоугольника
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

def upload(image, url):
# отправляем картинку по указанному url
    # session = requests.Session()
    data = arrayImage2json(image)
    try:
        r = post(url, data=data)
    except Exception:
        print("Error in connection to server")
    # session.close()

# обработка консольных параметров, перезапись констант, если они были переданы
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-wc', '--webcam', default=cameraSource)
    parser.add_argument('-dist', '--urlDist', default=urlDist)
    parser.add_argument('-kmin', default=kMinFace)
    parser.add_argument('-maxKadrEmpry', default=maxKadrEmpry)
    parser.add_argument('-kx', default=kx)
    parser.add_argument('-ky', default=ky)
    namespace = parser.parse_args(sys.argv[1:])
    cameraSource = namespace.webcam
    urlDist = namespace.urlDist
    kMinFace = float(namespace.kmin)
    maxKadrEmpry = int(namespace.maxKadrEmpry)
    kx = float(namespace.kx)
    ky = float(namespace.ky)

if type(cameraSource) == int: # for local
    video_capture = cv2.VideoCapture(cameraSource)
else: # for rtsp
    video_capture = cv2.VideoCapture(cameraSource, cv2.CAP_FFMPEG)

last_face_locations = []
cur_face_locations = []

kadrEmpty = 0
frame = None
while True:
    if cv2.waitKey(1) & 0xFF == 27:
        break
    ret, frame = video_capture.read()
    if not ret:
        print("Video doesn't accepted!")
        print(f"Address of webcam:  {cameraSource}")
        break
    else:
        # CAP_PROP_FOURCC = 875967080.0
        # CAP_PROP_CODEC_PIXEL_FORMAT = 808596553.0
        # ширина и высота экрана
        camWidth = video_capture.get(3)
        camHeight = video_capture.get(4)
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        #изменение размера, перевод картинки в формат rgb
        small_frame = cv2.resize(frame, (0, 0), fx=kx, fy=ky)
        #rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        rgb_small_frame = small_frame

        # определение координат лиц (прямоугольников)
        cur_face_locations = face_locations(rgb_small_frame)

        # заполнение массивов (для первого запуска)
        if not cur_face_locations:
            kadrEmpty += 1
            if kadrEmpty>maxKadrEmpry:
                last_face_locations = []
            cv2.imshow('Video', frame)
            continue
        else:
            kadrEmpty = 0

        # if not last_face_locations:
        #     last_face_locations = face_locations

        # отрисовка прямоугольников на экран
        # сравнение размера прямоугольника с минимальным
        for (top, right, bottom, left) in cur_face_locations:
            if 1/2*((bottom - top)/(camHeight*ky) + (right - left)/(camWidth*kx)) > kMinFace:
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= int(1/ky)
                right *= int(1/kx)
                bottom *= int(1/ky)
                left *= int(1/kx)
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # трекинг: поиск совпадений местонахождеий лиц а прошлом кадре
        # если найдено повторение - прекратить поиск
        # если нет ни одного повторения - вырезать и отправить лицо
        for newFace in cur_face_locations:
            for oldFace in last_face_locations:
                if differ(oldFace, newFace) < maxDistance:
                    break
            else:
                print(f"new face detect! {newFace}")
                [top, right, bottom, left] = [border*4 for border in newFace]
                imageToSend = frame[top:bottom, left:right]
                cv2.imshow(f"new face detect! {newFace}", imageToSend)
                imageToSend = cv2.cvtColor(imageToSend, cv2.COLOR_BGR2RGB)
                upload(imageToSend, urlDist)

        # текущий кадр становится прошлым, отрисовка окна видео
        last_face_locations = cur_face_locations
        cv2.imshow('Video', frame)



# закрываем видеопоток и окна
video_capture.release()
cv2.destroyAllWindows()



