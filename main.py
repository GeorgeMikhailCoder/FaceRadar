import cv2
import face_recognition
import requests
import sys
import argparse
from math import sqrt, pow
from time import sleep
# источник видеопотока, номер подключённой к системе камеры или ссылка на удалённую
# example:
# cameraSource = 0 # работает, локальная камера
# cameraSource = 'http://homecam:15243@192.168.43.1:8080/video' # работает, ip webcam, локальная сеть
# cameraSource = 'http://homecam:15243@10.243.165.231:8080/video' # не работает,  ip webcam, интернет
cameraSource = 0

# лица, занимающие меньше X% по среднему арифметическому отношений ширины и высоты к экрану отсеиваются
kMinFace = 0.1

# коэффициенты масштабирования входного изображения перед обработкой
kx = 0.25
ky = 0.25

maxDistance = 0.5
def differ(oldFace, newFace):
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



# обработка консольных параметров, перезапись констант, если они были переданы
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-wc', '--webcam', default=cameraSource)
    parser.add_argument('-kmin', default=kMinFace)
    parser.add_argument('-kx', default=kx)
    parser.add_argument('-ky', default=ky)
    namespace = parser.parse_args(sys.argv[1:])
    cameraSource = namespace.webcam
    kMinFace = float(namespace.kmin)
    kx = float(namespace.kx)
    ky = float(namespace.ky)

# video_capture = cv2.VideoCapture('rtsp://192.168.1.64/1')
video_capture = cv2.VideoCapture(cameraSource)

last_face_locations = []
face_locations = []
while True:
    ret, frame = video_capture.read()
    if not ret:
        print("Video doesn't accepted!")
        print(f"Address of webcam:  {cameraSource}")
        break
    else:
        # ширина и высота экрана
        camWidth = video_capture.get(3)
        camHeight = video_capture.get(4)

        small_frame = cv2.resize(frame, (0, 0), fx=kx, fy=ky)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        if not face_locations:
            continue
        if not last_face_locations:
            last_face_locations = face_locations

        for (top, right, bottom, left) in face_locations:
            if 1/2*((bottom - top)/(camHeight*ky) + (right - left)/(camWidth*kx)) > kMinFace:
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        for newFace in face_locations:
            for oldFace in last_face_locations:
                if differ(oldFace, newFace) < maxDistance:
                    break
            else:
                print("new face detect!")
        last_face_locations = face_locations
        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

print(face_locations)
video_capture.release()
cv2.destroyAllWindows()


def upload(image):
    session = requests.Session()
    url = '127.0.0.1'
    files = {'uploaded_photo': image}
    session.post(url, files=files)
    session.close()
