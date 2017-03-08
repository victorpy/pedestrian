import cv2
import pycurl
import sys
import numpy as np
from StringIO import StringIO
import argparse
from dbaccess import *

#'http://192.168.10.90/cgi-bin/snapshot.cgi?stream=1'

def line1(x,y):
	# (Bx-Ax)*(Cy-Ay)-(By-Ay)*(Cx-Ax)
	#[71, 383] [188, 345]
	val = (188-71)* (y-383) - (345-383) * (x-71)
	#print("line 1 ", val)
	return val

def line2(x,y):
	#[88, 439] [233, 387]
	val = (233-88)*(y-439) - (387-439) * (x-88)	
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
	
	grayscaleImage=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	#cv2.imshow('grayscaleImage',grayscaleImage)
	overlayImage=np.copy(grayscaleImage)


	cv2.drawContours(overlayImage,[pts],0,255)
	maskImage=np.zeros_like(grayscaleImage)
	cv2.drawContours(maskImage,[pts],0,255,-1)
	extractedImage=np.bitwise_and(grayscaleImage,maskImage)
	#cv2.imshow('extractedImage',extractedImage)

	img = cv2.bitwise_and(img,img, mask=maskImage)
	
	#pts = np.array([[10,150],[30,235],[160,235],[70,140]], np.int32)
	#pts = pts.reshape((-1,1,2))
	#cv2.polylines(img,[pts],True,(0,255,255))
	
	pointInMiddle = set()
	prev = points
	points = set()
	fgmask = img	
	#fgmask = cv2.blur(img, (10,10))
	fgmask =  cv2.GaussianBlur(img,(5,5),0)
	fgmask = fgbg.apply(fgmask) #, learningRate=0.01
	#erosion = cv2.erode(fgmask,None,iterations = 1);
	#dilation = cv2.dilate(erosion,None,iterations = 1);
	#cv2.imshow("dil", dilation)
	#fgmask = cv2.medianBlur(fgmask, 3)
	oldFgmask = fgmask.copy()
	
	#cv2.imshow("Mask", fgmask)
	
	image, contours, hierarchy = cv2.findContours(fgmask, cv2.RETR_EXTERNAL,1)
	for contour in contours:
		x,y,w,h = cv2.boundingRect(contour)		
		#if w>40 and h>90:
		if w>20 and h>30:
			#print(x,y,w,h)
			cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2, lineType=cv2.LINE_AA)
			point = (int(x+w/2.0), int(y+h/2.0))
			points.add(point)
    
	for point in points:
		(xnew, ynew) = point
		if line1(xnew, ynew) > 0 and line2(xnew, ynew) < 0:
			#print("in the middle")
			pointInMiddle.add(point)
		
		for prevPoint in prev:
			(xold, yold) = prevPoint
			dist = cv2.sqrt((xnew-xold)*(xnew-xold)+(ynew-yold)*(ynew-yold))
			#print(dist[0])
			if dist[0] <= 40:
				if line1(xnew, ynew) >= 0 and line2(xnew, ynew) <= 0:
					if line1(xold, yold) < 0: # Point entered from line below (1)
						pointFromBelow.add(point)
					elif line2(xold, yold) > 0:
						pointFromAbove.add(point)
					else:
						if prevPoint in pointFromBelow:
							pointFromBelow.remove(prevPoint)
							pointFromBelow.add(point)
						elif prevPoint in pointFromAbove:
							pointFromAbove.remove(prevPoint)
							pointFromAbove.add(point)
			#pointInMiddle.add(point)
				if line1(xnew, ynew) > 0 and prevPoint in pointFromBelow: # Point is above the line
					print('One Crossed A/B, sending to DB')					
					crossedAbove += 1
					print(crossedAbove)
					pointFromBelow.remove(prevPoint)
					insert_log(db,1,0)
					cv2.imwrite('/var/www/html/output/a_b.png',img)
					
				if line2(xnew, ynew) > 0 and prevPoint in pointFromAbove: # Point is below the line
					print('One Crossed B/A, sending to DB')
					crossedBelow += 1
					print(crossedBelow)
					pointFromAbove.remove(prevPoint)
					insert_log(db,0,1)
					cv2.imwrite('/var/www/html/output/b_a.png',img)
	
	
	#for point in points:
	#	cv2.circle(img, point, 3, (255,0,255),6)
	
	cv2.line(img, (71, 383), (188, 345), (255, 0, 0), 3)
	cv2.line(img, (88, 439), (233, 387), (255, 0, 0), 3)
	
	cv2.imwrite('/var/www/html/output/cvoutput.png',img)
	#cv2.imshow("Frame", img)
	key = cv2.waitKey(50) & 0xFF
	
	
	#if key == ord("q"):
	#		break

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()

