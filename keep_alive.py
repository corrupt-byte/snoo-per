from flask import Flask
from threading import Thread
import time # for the time delay so that we are certain it will work
app = Flask('')


# tell server its alive
@app.route('/')
def home():
    return "Operator, \nI'm alive and well" # made it sound alive

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():  
    t = Thread(target=run)
    t.start()
 
# tell you that it ran to avoid panic
time.sleep(3)
print("Message sent to server")
    
