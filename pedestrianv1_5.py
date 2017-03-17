import cv2
import pycurl
import sys
import numpy as np
from StringIO import StringIO
import argparse
import datetime
import time
from dbaccess import *

#'http://192.168.10.90/cgi-bin/snapshot.cgi?stream=1'

def line1(x,y):
	# (Bx-Ax)*(Cy-Ay)-(By-Ay)*(Cx-Ax)
	#[186, 163] [487, 185]
	val = (487-186)* (y-163) - (185-163) * (x-186)
	#print("line 1 ", val)
	return val

def line2(x,y):
	#[172, 357] [472, 389]
	val = (472-172)*(y-357) - (389-357) * (x-172)	
	#print("line2", val)
	return val


def read_from_url(url):

        buffer = StringIO()
        c = pycurl.Curl()
        c.setopt(c.URL,url )
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()
        #print(buffer.encode())
        img_array = np.asarray(bytearray(buffer.getvalue()), dtype=np.uint8 )
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        return img



ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-u", "--url", help="url path")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
args = vars(ap.parse_args())


# if the video argument is None, then we are reading from webcam
if args.get("url", None) is None:
	print("no url argument")
	sys.exit()

print("connecting to DB")
db = connectDB()


print("Starting Capture")

dim = (640,480)

points = set()
pointFromBelow = set()
pointFromAbove = set()
crossedAbove = 0
crossedBelow = 0

fgbg = cv2.createBackgroundSubtractorMOG2()
#pts = np.array([[10,150],[30,235],[160,235],[70,140]], np.int32)
#ROI
pts = np.array([[10,250],[30,470],[350,470],[70,230]], np.int32)

# loop over the frames of the video
while True:

	# text
	img = read_from_url(args["url"])
	
	img = cv2.resize(img, dim)
	
	hsvImage=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
	h = hsvImage[:,:,0]
	
	grayscaleImage=h
	#cv2.imshow('grayscaleImage',grayscaleImage)
	overlayImage=np.copy(grayscaleImage)

		
	#pts = np.array([[10,150],[30,235],[160,235],[70,140]], np.int32)
	#pts = pts.reshape((-1,1,2))
	#cv2.polylines(img,[pts],True,(0,255,255))
	
	pointInMiddle = set()
	prev = points
	points = set()
	fgmask = grayscaleImage
	#fgmask = cv2.blur(img, (10,10))
	fgmask =  cv2.GaussianBlur(fgmask,(5,5),0)
	fgmask = fgbg.apply(fgmask, learningRate=0.04) #, learningRate=0.01
	erosion = cv2.erode(fgmask,None,iterations = 1);
	dilation = cv2.dilate(erosion,None,iterations = 1);
	#cv2.imshow("dil", dilation)
	#fgmask = cv2.medianBlur(fgmask, 3)
	oldFgmask = fgmask.copy()
	
	#cv2.imshow("Mask", fgmask)
	
	image, contours, hierarchy = cv2.findContours(fgmask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	
	for contour in contours:
		x,y,w,h = cv2.boundingRect(contour)		
		#if w>40 and h>90:
		if w>100 and h>100:
			#print(x,y,w,h)
			cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2, lineType=cv2.LINE_AA)
			point = (int(x+w/2.0), int(y+h/2.0))
			points.add(point)
    
	for point in points:
		(xnew, ynew) = point
		if line1(xnew, ynew) > 0 and line2(xnew, ynew) < 0:
			#print("in the middle")
			pointInMiddle.add(point)
			crossedAbove += 1
			print(crossedAbove)
			#pointFromBelow.remove(prevPoint)
			insert_log(db,1,0)
			cv2.putText(img, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
(10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
			cv2.imwrite('/var/www/html/output/a_b'+str(crossedAbove)+'.png',img)
		
			
	
	#for point in points:
	#	cv2.circle(img, point, 3, (255,0,255),6)
	
	cv2.line(img, (186, 163), (487, 185), (255, 0, 0), 3)
	cv2.line(img, (172, 357), (472, 389), (255, 0, 0), 3)
	
	cv2.imwrite('/var/www/html/output/cvoutput.png',img)
	#cv2.imshow("Frame", img)
	key = cv2.waitKey(50) & 0xFF
	
	
	#if key == ord("q"):
	#		break

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()

