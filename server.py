#  coding: utf-8 
import socketserver
#
import time
import os
import sys


# Copyright 2013 Abram Hindle, Eddie Antonio Santos, Tianqi Wang
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

ROOT = './www'

class BadRequestError(Exception):
    pass
class MethodNotAllowedError(Exception):
    pass
class NotFoundError(Exception):
    pass
class MovedPermanentlyError(Exception):
    pass
class ForbiddenError(Exception):
    pass

class MyWebServer(socketserver.BaseRequestHandler):
    
    def handle(self):
        self.data = self.request.recv(1024).strip()
        
        try:
            request = Parser(self.data)
            
        except BadRequestError as e:
            contents = self._generate_html(str(e))
            header = self._generate_headers(400, {
                'Content-Type': 'text/html',
                'Content-Length': len(contents),
            })
            self.request.sendall(
                bytearray(
                    header + contents,'utf-8'
                )
            )
            return
            
        except MethodNotAllowedError:
            header = self._generate_headers(405)
            self.request.sendall(
                bytearray(
                    header,'utf-8'
                )
            )
            return
        
        except MovedPermanentlyError as e:
            header = self._generate_headers(301, {'Location': str(e)+'/'})
            self.request.sendall(
                bytearray(
                    header,'utf-8'
                )
            )
            return
        
        except ForbiddenError:
            contents = self._generate_html("<H1>Fobidden</H1>")
            header = self._generate_headers(403, {
                'Content-Type': 'text/html',
                'Content-Length': len(contents),
            })
            
            self.request.sendall(
                bytearray(
                    header + contents,'utf-8'
                )
            )
            return
        
        
        location = request.getLocation()
        if location[-1] == '/':
            location = location + 'index.html'
        file_type= location.split(".")[-1]
        if file_type == 'html':
            type = 'text/html'
        elif file_type == 'css':
            type = 'text/css'
        else:
            contents = self._generate_html("<H1>Fobidden</H1>")
            header = self._generate_headers(403, {
                'Content-Type': 'text/html',
                'Content-Length': len(contents),
            })
            
            self.request.sendall(
                bytearray(
                    header + contents,'utf-8'
                )
            )
            return
        
        try:
            file = open(ROOT + location, "r")
            if file.mode == 'r':
                contents = file.read()
                self.request.sendall(
                    bytearray(
                        self._generate_headers(200, {
                            'Content-Type': type,
                            'Content-Length': len(contents),
                        })+contents, 'utf-8'
                    )
                )
        except FileNotFoundError:
            self.request.sendall(
                bytearray(
                    self._generate_headers(404), 'utf-8'
                )
            )
        
    def _generate_html(self, data):
        return "<html><body>{}</body></html>".format(data)
        
    def _generate_headers(self, code, params={}):
        header = ''
        if code == 200:
            header += 'HTTP/1.1 200 OK\r\n'
            #header += 'Content-Type: {}\r\n'.format(params['Content-Type'])
        elif code == 301:
            header += 'HTTP/1.1 301 Moved Permanently\r\n'
            #header += 'Location: {}\r\n'.format(params['Location'])
        elif code == 400:
            header += 'HTTP/1.1 400 Bad Request\r\n'
        elif code == 403:
            header += 'HTTP/1.1 403 Forbidden\r\n'
        elif code == 404:
            header += 'HTTP/1.1 404 Not Found\r\n'
        elif code == 405:
            header += 'HTTP/1.1 405 Method Not Allowed\r\n'
        for param in params:
            header += '{}: {}\r\n'.format(param, params[param])
        time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        header += 'Date: {now}\r\n'.format(now=time_now)
        header += 'Server: A partially HTTP 1.1 compliant webserver\r\n'
        header += 'Connection: close\r\n\r\n'
        return header

class Parser():
    def __init__(self, msg):
        self.msg = msg.decode("utf-8")
        print(self.msg)
        
        request, headers = self.msg.split('\r\n', 1)
        self.location = self._getLocation(request)
            
        
        print(request)
        # construct a message from the request string
        # message = email.message_from_file(StringIO(headers))
        # construct a dictionary containing the headers
        # self.headers = dict(message.items())

    #def getHeader(self):
        #return self.headers
        
    def getLocation(self):
        return self.location
        
    def _getLocation(self, request):
        parts = request.split()
        try:
            method, location, protocol = parts
            temp = location.split(".")
            if len(temp) == 1:
                if location[-1] != '/':
                    raise MovedPermanentlyError(location)
            else:
                if '/' in temp[-1]:
                    raise MovedPermanentlyError(location)
                    
            if not os.path.realpath(location).startswith("/"):
                raise ForbiddenError()

#            if len(location) > len('\www'):
#                if location[:4] != '\www':
#                    raise ForbiddenError
            
        except ValueError:
            raise BadRequestError()
        except IndexError:
            raise BadRequestError()
        
        if method != 'GET':
            raise MethodNotAllowedError()
        if protocol != 'HTTP/1.1':
            raise BadRequestError('I only understand HTTP/1.1')
        return location


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
