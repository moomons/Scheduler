
from pycon_cfg import *
import threading


# multi-threading class
class MyThread(threading.Thread):
    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args

    def run(self):
        self.res = apply(self.func, self.args)

    def getResult(self):
        return self.res


# def getPortRate():
#     print 'Hello'
#
#
# # Monitor port rate
# t2 = MyThread(getPortRate, [2], "RX/TX Calc")
# t2.isDaemon()
# t2.setDaemon(True)
# t2.start()

