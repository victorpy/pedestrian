#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  demo.py
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the project nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import logging
import sys
import cv2
from PIL import Image
import StringIO
import time

from advancedhttpserver import *
from advancedhttpserver import __version__

#1 rtsp with url, 2 webcam 0
def open_capture(captype,url=''):
	
	if captype == 1:
		#url = "rtsp://192.168.10.91:554/h264cif?username=admin&password=123456"
		vcap = cv2.VideoCapture(url)
		capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320); 
		capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240);
		capture.set(cv2.CAP_PROP_SATURATION,0.2);
		return vcap
	
	if captype == 2:
		capture = cv2.VideoCapture(0)
		capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320); 
		capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240);
		capture.set(cv2.CAP_PROP_SATURATION,0.2);
		return capture

class DemoHandler(RequestHandler):
		
	def on_init(self):
		print("on init")
		self.handler_map['^redirect_to_google$'] = lambda handler, query: self.respond_redirect('http://www.google.com/')
		self.handler_map['^hello_world$'] = self.res_hello_world
		self.handler_map['^exception$'] = self.res_exception
		self.handler_map['^cam$'] = self.res_cam
		self.handler_map['^rtsp$'] = self.res_rtsp

		self.rpc_handler_map['/xor'] = self.rpc_xor

	def res_hello_world(self, query):
		message = 'Hello World!\r\n\r\n'
		self.send_response(200)
		self.send_header('Content-Length', len(message))
		self.end_headers()
		if self.basic_auth_user:
			self.wfile.write('Username: ' + self.basic_auth_user + '\r\n')
		self.wfile.write(message.encode("utf-8"))
		#return
		
	def res_cam(self, query):

		capture = open_capture(2)
		
		self.send_response(200)
		self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
		self.end_headers()
		while True:
			try:
				rc,img = capture.read()
				if not rc:
					continue
				imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
				jpg = Image.fromarray(imgRGB)
				tmpFile = StringIO.StringIO()
				jpg.save(tmpFile,'JPEG')
				self.wfile.write("--jpgboundary")
				self.send_header('Content-type','image/jpeg')
				self.send_header('Content-length',str(tmpFile.len))
				self.end_headers()
				jpg.save(self.wfile,'JPEG')
				time.sleep(0.05)
			except KeyboardInterrupt:
				break
			except IOError:
				capture.release()
				print("IOERROR")
				break
				
	def res_rtsp(self, query):
		
		capture = open_capture(1,"rtsp://192.168.10.91:554/h264cif?username=admin&password=123456")
		
		self.send_response(200)
		self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
		self.end_headers()
		while True:
			try:
				rc,img = capture.read()
				if not rc:
					continue
				imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
				jpg = Image.fromarray(imgRGB)
				tmpFile = StringIO.StringIO()
				jpg.save(tmpFile,'JPEG')
				self.wfile.write("--jpgboundary")
				self.send_header('Content-type','image/jpeg')
				self.send_header('Content-length',str(tmpFile.len))
				self.end_headers()
				jpg.save(self.wfile,'JPEG')
				time.sleep(0.05)
			except KeyboardInterrupt:
				break
			except IOError:
				capture.release()
				print("IOERROR")
				break			
	
	def finish_request(self):
		capture.release() 

	def rpc_xor(self, key, data):
		return ''.join(map(lambda x: chr(ord(x) ^ key), data))

	def res_exception(self, query):
		raise Exception('this is an exception, oh noes!')


def main():
	print("AdvancedHTTPServer version: {0}".format(__version__))
	logging.getLogger('').setLevel(logging.DEBUG)
	console_log_handler = logging.StreamHandler()
	console_log_handler.setLevel(logging.INFO)
	console_log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
	logging.getLogger('').addHandler(console_log_handler)
	global viewer
	viewer=0
	#global capture
	#capture = cv2.VideoCapture(0)
	#capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320); 
	#capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240);
	#capture.set(cv2.CAP_PROP_SATURATION,0.2);

	server = AdvancedHTTPServer(DemoHandler)
	#server.auth_add_creds('demouser', 'demopass')
	server.server_version = 'AdvancedHTTPServerDemo'
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		server.shutdown()
	return 0

if __name__ == '__main__':
	main()
