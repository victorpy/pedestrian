# pedestrian
People counter with python 2.7 and opencv 2.4 for raspberry pi 3

Program 
Read images from raspberry pi camera
Cut the image in the area of interest
Apply BGS algorithm to image
Find blobs
Track the blob
If it goes from point A to Point B crossing a line, the blob gets counted
Send a log to a mysql database for every count

