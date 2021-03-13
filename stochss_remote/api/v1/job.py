from flask import Flask, Blueprint

job = Blueprint("job", __name__, url_prefix="/job")

@job.route("/create")
def create():
    

@job.route("/{id}")
def info(id):

@job.route("/{id}/start")
def start(id):

class JobCreate(object):
    def __init__(self, id):
        self.id = id
