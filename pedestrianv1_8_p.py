import numpy as np
import cv2
from imutils.video import FileVideoStream
from imutils.video import FPS
import time
import Person
from io import BytesIO
import pycurl
import urllib
import datetime

mask_pts = np.array([[180, 4],[365, 2], [334, 273], [155, 268]], np.int32)

def mask_image(img,pts):
#[365, 2] [334, 273]
#[180, 4] [155, 268]

	out_img = np.copy(img)
	grayscaleImage=cv2.cvtColor(out_img,cv2.COLOR_BGR2GRAY)
	overlayImage=np.copy(grayscaleImage)


	cv2.drawContours(overlayImage,[pts],0,255)
	maskImage=np.zeros_like(grayscaleImage)
	cv2.drawContours(maskImage,[pts],0,255,-1)
	extractedImage=np.bitwise_and(grayscaleImage,maskImage)

	out_img = cv2.bitwise_and(out_img,out_img, mask=maskImage)
	
	return out_img
	
def img_preprocessing(img):
	
	ret,imBin = cv2.threshold(img,200,255,cv2.THRESH_BINARY)
	
	imBin = cv2.blur(imBin,(5,5))

	mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp, iterations=3)
	mask= cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernelCl, iterations=4)
	
	return mask
	
	
def read_from_url(url):

	url = urllib.urlopen("http://192.168.10.91/cgi-bin/snapshot.cgi?stream=0")
	arr = np.asarray(bytearray(url.read()), dtype=np.uint8)
	img = cv2.imdecode(arr,-1) # 'load it as it is'
        #print(img.shape)
	return img

def read_from_rtsp(vcap):

	ret, frame = vcap.read()
	return frame


print("[{0}][INFO] starting person counter... ".format(time.strftime("%D %T")))
#fvs = FileVideoStream('upcamvid.avi', queueSize=910).start()
#fvs = FileVideoStream("rtsp://192.168.10.91:554/h264?username=admin&password=123456", queueSize=910).start()
#time.sleep(1.0)

w = 146
h = 202
frameArea = h*w
#areaTH = frameArea/250
#areaTH = 2000
#print('Area Threshold', areaTH)

#Lineas de entrada/salida
line_up = int(2*(h/5))
line_down   = int(3*(h/5))

up_limit =   int(1*(h/6))
down_limit = int(5*(h/6))

print("Red line y:",str(line_down))
print("Blue line y:", str(line_up))
line_down_color = (255,0,0)
line_up_color = (0,0,255)
pt1 =  [0, line_down];
pt2 =  [w, line_down];
pts_L1 = np.array([pt1,pt2], np.int32)
pts_L1 = pts_L1.reshape((-1,1,2))
pt3 =  [0, line_up];
pt4 =  [w, line_up];
pts_L2 = np.array([pt3,pt4], np.int32)
pts_L2 = pts_L2.reshape((-1,1,2))

pt5 =  [0, up_limit];
pt6 =  [w, up_limit];
pts_L3 = np.array([pt5,pt6], np.int32)
pts_L3 = pts_L3.reshape((-1,1,2))
pt7 =  [0, down_limit];
pt8 =  [w, down_limit];
pts_L4 = np.array([pt7,pt8], np.int32)
pts_L4 = pts_L4.reshape((-1,1,2))


print("[{0}][INFO] creating BGS... ".format(time.strftime("%D %T")))

fgbg = cv2.createBackgroundSubtractorMOG2(varThreshold=120)#history=100, varThreshold=100, detectShadows = True) #Create the background substractor

#Create the background substractor
kernelOp = np.ones((5,5),np.uint8)
kernelCl = np.ones((15,15),np.uint8)
areaTH = 2200
#Variables
font = cv2.FONT_HERSHEY_SIMPLEX
persons = []
max_p_age = 4
pid = 1
#Contadores de entrada y salida
cnt_up   = 0
cnt_down = 0

#count how many times read() returns false
falseRetCounter=0
maxFrameError=15 #for 15 fps is one second

#dim = (480,270)
dim = (360,202)

print("[{0}][INFO] Opening video stream... ".format(time.strftime("%D %T")))

url = "rtsp://192.168.10.91:554/h264cif?username=admin&password=123456"
vcap = cv2.VideoCapture(url)
fps = vcap.get(cv2.CAP_PROP_FPS); 

print("[{0}][INFO] video stream fps {1} ".format(time.strftime("%D %T"), fps))

###train###
#cap = cv2.VideoCapture('upcamrtsp.avi') #Open video file

#while cap.isOpened():
#    try:
#        frame = cv2.resize(frame, dim)
        #crop image keep from y line 118 to line 264  for image shape (360,202) 
#        frame = frame[:, 118:264]
#    except  Exception as e:
#        print(str(e))
#        break
        
#    fgmask = fgbg.apply(frame)#, learningRate=0.05) #Use the substractor
	
#cap.release() 

#cap = cv2.VideoCapture('upcamvid.avi') #Open video file

# start the FPS timer
print("[{0}][INFO] starting fps timer ".format(time.strftime("%D %T")))
fps = FPS().start()

#while fvs.more():
while vcap.isOpened():
#while True:

    #a = datetime.datetime.now()
    ret, frame = vcap.read()
    #frame = read_from_url('http://192.168.10.91/cgi-bin/snapshot.cgi?stream=0')
    #frame = read_from_rtsp(vcap)
    #frame = fvs.read()
    
    if ret==False:
        falseRetCounter += 1
        if falseRetCounter < maxFrameError:
            print("[{0}][ERROR] Too many false returns in read, goind down ".format(time.strftime("%D %T")))
            break
        else:
            continue
    
    for i in persons:
        i.age_one() #age every person one frame
    
    try:
        frame = cv2.resize(frame, dim)        
        frame = frame[:, 118:264]
        
        frame = cv2.GaussianBlur(frame, (5, 5), 0)
        fgmask = fgbg.apply(frame, learningRate=0.036) #Use the substractor
        
        mask = img_preprocessing(fgmask)
        
    except  Exception as e:
        print(str(e))
        break
    
    _, contours0, hierarchy = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    for cnt in contours0:
        #cv2.drawContours(frame, cnt, -1, (0,255,0), 3, 8)
        area = cv2.contourArea(cnt)
        #print(area)
        if area > areaTH:
            #################
            #   TRACKING    #
            #################            
            M = cv2.moments(cnt)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            x,y,w,h = cv2.boundingRect(cnt)
            
            new = True
            if cy in range(up_limit,down_limit):
	            for i in persons:
	                if abs(x-i.getX()) <= w and abs(y-i.getY()) <= h:
	                    # el objeto esta cerca de uno que ya se detecto antes
	                    new = False
	                    i.updateCoords(cx,cy)   #actualiza coordenadas en el objeto and resets age
	                    
	                    if i.going_UP(line_down,line_up) == True:
	                        cnt_up += 1;
	                        print("[INFO] ID:",i.getId(),'crossed going up at',time.strftime("%c"))
	                        index = persons.index(i)
	                        persons.pop(index)
	                        del i     #liberar la memoria de i
				cv2.imwrite('/var/www/html/output/up'+str(cnt_up)+'.png',frame)
				print('UP: '+ str(cnt_up))
	                    elif i.going_DOWN(line_down,line_up) == True:
	                        cnt_down += 1;
	                        print ("[INFO] ID:",i.getId(),'crossed going down at',time.strftime("%c"))
	                        index = persons.index(i)
	                        persons.pop(index)
	                        del i     #liberar la memoria de i
				cv2.imwrite('/var/www/html/output/down'+str(cnt_down)+'.png',frame)
				print('DOWN: '+ str(cnt_down))
	                    break
	                    
                        if i.getState() == '1':
                            if i.getDir() == 'down' and i.getY() > down_limit:
                                i.setDone()
                            elif i.getDir() == 'up' and i.getY() < up_limit:
                                i.setDone()
                        if i.timedOut():
                            #sacar i de la lista persons
                            index = persons.index(i)
                            persons.pop(index)
                            del i     #liberar la memoria de i

	            if new == True:
	                p = Person.MyPerson(pid,cx,cy, max_p_age)
	                persons.append(p)
	                pid += 1 
           
            #################
            #   DIBUJOS     #
            #################
            #cv2.circle(frame,(cx,cy), 5, (0,0,255), -1)
            #img = cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)            
            #cv2.drawContours(frame, cnt, -1, (0,255,0), 3)

    #########################
    # DIBUJAR TRAYECTORIAS  #
    #########################
    #for i in persons:
        #if len(i.getTracks()) >= 2:
            #pts = np.array(i.getTracks(), np.int32)
            #pts = pts.reshape((-1,1,2))
            #frame = cv2.polylines(frame,[pts],False,i.getRGB())
        #if i.getId() == 9:
            #print(str(i.getX()), ',', str(i.getY()))
    #    cv2.putText(frame, str(i.getId()),(i.getX(),i.getY()),font,0.3,i.getRGB(),1,cv2.LINE_AA)
    
    
    #str_up = 'UP: '+ str(cnt_up)
    #str_down = 'DOWN: '+ str(cnt_down)
    #frame = cv2.polylines(frame,[pts_L1],False,line_down_color,thickness=2)
    #frame = cv2.polylines(frame,[pts_L2],False,line_up_color,thickness=2)
    #frame = cv2.polylines(frame,[pts_L3],False,(255,255,255),thickness=1)
    #frame = cv2.polylines(frame,[pts_L4],False,(255,255,255),thickness=1)
    #cv2.putText(frame, str_up ,(10,40),font,0.5,(255,255,255),2,cv2.LINE_AA)
    #cv2.putText(frame, str_up ,(10,40),font,0.5,(0,0,255),1,cv2.LINE_AA)
    #cv2.putText(frame, str_down ,(10,90),font,0.5,(255,255,255),2,cv2.LINE_AA)
    #cv2.putText(frame, str_down ,(10,90),font,0.5,(255,0,0),1,cv2.LINE_AA)
            
    #cv2.imshow('Frame',frame)

	#Abort and exit with 'Q' or ESC
    k = cv2.waitKey(1) & 0xff
    fps.update()
    #if k == 27:
    #    break
    #b = datetime.datetime.now()
	# stop the timer and display FPS information
    #print("diff", b-a)
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

#cap.release() #release video file
cv2.destroyAllWindows() #close all openCV windows

