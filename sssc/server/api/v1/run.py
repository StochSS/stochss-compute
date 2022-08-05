from tornado.web import RequestHandler
import json

class RunHandler(RequestHandler):
    def post(self):
        self.write(self.request.body)
        
        print(self.request.body)
