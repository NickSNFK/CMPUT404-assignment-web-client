#!/usr/bin/env python3
# coding: utf-8
# Copyright 2023 Abram Hindle, https://github.com/tywtyw2002, https://github.com/treedust,
# and Nicholas Wielgus
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
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

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

ALLOWED_SCHEMES = {'http':80}
HEADER_DELIM = '\r\n'
MESSAGE_END = '\r\n\r\n'

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    #def get_host_port(self,url):

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        try:
            #get the frist line of response
            req_type = str(data).split(HEADER_DELIM)[0]
            # get to first "word" and convert to integer
            status = req_type.split()[1]
            return int(status)
        except:
            return 500

    def get_headers(self,data):
        try:
            # get all lines after first and sepperate with a new line
            headers = str(data).split(MESSAGE_END)[0].split(HEADER_DELIM)
            headers = headers[1:]
            return '\n'.join(headers)
        except:
            return ''


    def get_body(self, data):
        try:
            # get everything after double return new line
            return str(data).split(MESSAGE_END)[1]
        except:
            return ''

    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    # check the provided url and returns the proper host, port, request to send, Otherwise return none
    def check_valid(self, req_type, url, args):
        #break up url into parts
        parts_of_url = urllib.parse.urlparse(url)

        url_scheme = parts_of_url.scheme
        url_host = parts_of_url.hostname
        url_port = parts_of_url.port
        url_path = parts_of_url.path

        #port not found
        if not url_port:
            # check scheme against supported, ex: http
            if url_scheme in ALLOWED_SCHEMES.keys():
                # set port to supported port for scheme
                url_port = int(ALLOWED_SCHEMES.get(url_scheme))
            else:
                # scheme unsupported
                return None
        if not url_path:
            # path not found
            # default to '/'
            url_path = '/'

        _headers = {}
        _headers.update(
            {
                'Host': url_host,
                'Connection': 'close'
            }
        )

        #build request
        request_type = ' '.join([f'{req_type}',f'{url_path}', 'HTTP/1.1'])

        request_body = ''

        # handle if post
        if req_type == 'POST':
            if args:
                # args found
                request_body = urllib.parse.urlencode(args)
            else:
                request_body = urllib.parse.urlencode('')
            # add content-type and length
            _headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': str(len(request_body))
            })

        #seperate each header with return and new line
        request_headers = HEADER_DELIM.join(f'{key}: {_headers.get(key)}' for key in _headers.keys())

        # build final request to send
        final_request = \
            request_type + HEADER_DELIM + \
            request_headers +  MESSAGE_END + \
            request_body

        return (url_host, url_port, final_request)

    def send_request(self, host, port, request):
        try:
            # connect
            self.connect(host,port)
            # send request
            self.sendall(request)
            # receive request
            response = self.recvall(self.socket)
            code = self.get_code(response)
            body = self.get_body(response)
            headers = self.get_headers(response)
        finally:
            self.close()
        return HTTPResponse(code,body)

    def GET(self, url, args=None):
        # validate request
        validated_request = self.check_valid('GET',url,args)
        if not validated_request:
            # reqeust issue, https etc.
            return HTTPResponse(400, '')
        response = self.send_request(validated_request[0],
                                     validated_request[1],
                                     validated_request[2])
        code = response.code
        body = response.body
        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        # validate request
        validated_request = self.check_valid('POST',url,args)
        if not validated_request:
            # reqeust issue, https etc.
            return HTTPResponse(400, '')
        response = self.send_request(validated_request[0],
                                     validated_request[1],
                                     validated_request[2])
        code = response.code
        body = response.body
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )

if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
