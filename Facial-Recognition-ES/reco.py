#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 23:35:12 2017

@author: pandipool
"""

import cv2, sys, numpy, os
import pymysql
import tkinter
from datetime import datetime

#Abrir conexión a BD
db = pymysql.connect("localhost","root","","asistencia_personal_eagles")

#Prepare un cursor
cursor = db.cursor()

#Ubicar las rutas de los archivos y carpetas
size = 4
fn_haar = 'haarcascade_frontalface_alt.xml'
fn_dir = 'att_faces\orl_faces'

#Creando fisherRecognizer
print('Entrenando...')

#Crear una lista de imagenes y una lista de nombres correspondientes
(images, lables, names, id) = ([], [], {}, 0)
for (subdirs, dirs, files) in os.walk(fn_dir):
    for subdir in dirs:
        names[id] = subdir
        subjectpath = os.path.join(fn_dir, subdir)
        for filename in os.listdir(subjectpath):
            path = subjectpath + '/' + filename
            lable = id
            images.append(cv2.imread(path, 0))
            lables.append(int(lable))
        id += 1
(im_width, im_height) = (112, 92)

#Crear una matriz Numpy de las dos listas anteriores
(images, lables) = [numpy.array(lis) for lis in [images, lables]]

#OpenCV entrena un modelo a partir de las imagenes
model = cv2.face.FisherFaceRecognizer_create()
model.train(images, lables)

#Utilizar fisherRecognizer en funcionamiento la camara
haar_cascade = cv2.CascadeClassifier(fn_haar)

#Cargar los controladores de la cámara
wecam_port2 = 0
webcam = cv2.VideoCapture(wecam_port2,cv2.CAP_DSHOW)

#Tomar el número de muestras para el reconocimiento de patrones
def reco():
    count = 0
    es_personal = 0
    while True:
        (rval, frame) = webcam.read()
        frame= cv2.flip(frame,1,0)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mini = cv2.resize(gray, (int(gray.shape[1] / size), int(gray.shape[0] / size)))
        faces = haar_cascade.detectMultiScale(mini)
        for i in range(len(faces)):
            face_i = faces[i]
            (x, y, w, h) = [v * size for v in face_i]
            face = gray[y:y + h, x:x + w]
            face_resize = cv2.resize(face, (im_width, im_height))
        
            # Intentando reconocer la cara
            prediction = model.predict(face_resize)
            
            #Ventana que encierra la ROI
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        
            #La variable cara tendra el nombre de la persona reconocida  
            es_personal = '%s' % (names[prediction[0]])
            print(es_personal)
                    
            #Count asegura un buen reconocimiento del rostro
            if count > 10 and count <95:
                cv2.putText(frame, str(count) + ' Bienvenid@ ' + '%s - %.0f' % (names[prediction[0]],prediction[1]),(x-10, y-10), cv2.FONT_HERSHEY_PLAIN,1,(0, 255, 0))
                
                #Fecha y hora del registro
                fecha_hora = datetime.now()
                fecha = fecha_hora.strftime('%Y-%m-%d')
                hora = fecha_hora.strftime('%H:%M:%S')
                
                if count == 90:
                    #Llamamos al SP que devuelve la última marca
                    cursor.callproc("ASISTENCIA_EMPLEADO_ESTADO", args=[str(es_personal)])
                    marca = cursor.fetchall()
                    print(marca, type(marca))
                    print(marca[0][1], type(marca[0][1]))
                    print(marca[0][2], type(marca[0][2]))
                    print(fecha, type(fecha))
                    
                    if marca[0][1] == None and str(marca[0][2]) == fecha:
                        insert = "INSERT INTO asistencia_empleado (dni, fecha_asistencia, hora_asistencia, tipo_marcacion) VALUES ('%s', '%s', '%s', 'E')" % (es_personal, fecha, hora)
                    
                        try:
                            #Ejecutar la query
                            cursor.execute(insert)
                            #Commit de los cambios en BD
                            db.commit()
                        except:
                            #Rollback en caso de error
                            db.rollback()
                    elif marca[0][1] == 'E' and str(marca[0][2]) == fecha:
                        insert = "INSERT INTO asistencia_empleado (dni, fecha_asistencia, hora_asistencia, tipo_marcacion) VALUES ('%s', '%s', '%s', 'S')" % (es_personal, fecha, hora)
                        
                        try:
                            #Ejecutar la query
                            cursor.execute(insert)
                            #Commit de los cambios en BD
                            db.commit()
                        except:
                            #Rollback en caso de error
                            db.rollback()
                    else:
                        
                        try:
                            #Commit de los cambios en BD
                            db.commit()
                        except:
                            #Rollback en caso de error
                            db.rollback()
            
            #Pantalla de logo Eagles Safety
            if count <= 10:
                img = cv2.imread("eagles_logo.png")
                cv2.imshow('Eagles Safety', img)
                key = cv2.waitKey(10)
                if key == 27:
                    break
            else:
                cv2.imshow('Eagles Safety', frame)
                key = cv2.waitKey(10)
                if key == 27:
                    break
            
            #Si no reconoce un rostro, count se reinicia
            if prediction[1] > 600:
                count = 0
            else:
                cv2.putText(frame, str(count), (x-10, y-10), cv2.FONT_HERSHEY_PLAIN,1,(0, 255, 0))
                count +=1
        #Finalizamos ciclo While
        if count == 91:
            cv2.destroyAllWindows()
            break

#GUI Marcar asistencia
top = tkinter.Frame(height = 480, width = 640)
top.pack(padx = 20, pady = 20)

#Botón que inicia reconocimiento llamando la función
tkinter.Button(top, text = '¡Marca tu asistencia!', command = reco).place(x = 100, y = 150)

#Etiqueta de título
etiqueta = tkinter.Label(top, text = 'BIENVENIDO A EAGLES SAFETY', font = ('Verdana', 20)).place(x = 95, y = 20)

top.mainloop()