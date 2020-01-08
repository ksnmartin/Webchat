import socket
import ssl
import cv2
from PIL import Image,ImageTk
import concurrent.futures
import pickle
import wave
import pyaudio
import numpy as np
import threading as th
import tkinter as tk

class server():

    def __init__(self, arg):
        self.arg = arg
        self.Local_Server_incoming = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.Local_Server_outgoing = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.Incoming_request_address_array = []
        self.Incoming_request_socket_array =[]


    def create_server(self,address_in,address_out):
        self.Local_Server_incoming.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.Local_Server_outgoing.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.Local_Server_incoming.bind(address_in)
        self.Local_Server_outgoing.bind(address_out)
        self.Local_Server_incoming.listen(5)

    def connector(self):
         print("wiat")
         while True:
             addr , sock = self.Local_Server_incoming.accept()
             self.Incoming_request_socket_array.append(sock)
             self.Incoming_request_address_array.append(addr)


class Aud_Vid():

    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.CHUNK = 1470
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.audio = pyaudio.PyAudio()
        self.instream = self.audio.open(format=self.FORMAT,channels=self.CHANNELS,rate=self.RATE,input=True,frames_per_buffer=self.CHUNK)
        self.outstream = self.audio.open(format=self.FORMAT,channels=self.CHANNELS,rate=self.RATE,output=True,frames_per_buffer=self.CHUNK)
    
    def sync(self):
         with concurrent.futures.ThreadPoolExecutor() as executor:
                 tv = executor.submit(self.video.read)
                 ta = executor.submit(self.instream.read,1470)
                 vid = tv.result()
                 aud = ta.result()
                 return(vid,aud)



class GUI(server,Aud_Vid):

    def __init__(self, networks, graphics):
        self.server = networks
        self.avi = graphics
        self.Application_Window = tk.Tk()
        self.Application_Window.title("WebChat")
        self.width = self.Application_Window.winfo_screenwidth()
        self.height = self.Application_Window.winfo_screenheight()
        self.para = self.server.Incoming_request_address_array
        self.Application_Window.geometry('%dx%d+0+0' % (self.width,self.height))
        self.m3nu = tk.Menu(self.Application_Window)
        self.Application_Window.config(menu=self.m3nu)
        self.Incoming = tk.Menu(self.m3nu)
        self.m3nu.add_cascade(label='Incoming requests', menu=self.Incoming)
        self.error_indicator = 'status'
        self.error_label = tk.Label(self.Application_Window,text=self.error_indicator)
        imgop = Image.open("pico_img.png")
        img = ImageTk.PhotoImage(imgop)
        self.ImageMain = tk.Label(self.Application_Window,image = img)
        self.ImageMain.image = img
        imgop1 = Image.open("lenna.png")
        img1 = ImageTk.PhotoImage(imgop1)
        self.ImageRecv = tk.Label(self.Application_Window,image = img1)
        self.ImageRecv.image = img1
        self.ip_enter = tk.Entry(self.Application_Window)
        self.port_enter = tk.Entry(self.Application_Window)
        self.make_call_button =  tk.Button(self.Application_Window,text = 'make call' ,command = self.make_call)
        self.end_call_button =  tk.Button(self.Application_Window,text = 'end call' ,command = self.end_call)
        self.ip_enter.grid(row=0, column=1)
        self.port_enter.grid(row=1, column=1)
        self.make_call_button.grid(row=3, column=1)
        self.error_label.grid(row=4, column=1)
        self.ImageMain.grid(row=5, column=1)
        self.ImageRecv.grid(row=5,column=3)
        self.end_call_button.grid(row = 6 , column =1)
        self.tshopic = th.Thread(target=self.show_picture)
        self.tcon = th.Thread(target=self.server.connector)
        self.tshopic.start()
        self.tcon.start()

    def show_picture(self):
        ret,frame = self.avi.video.read()
        pi = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pic =  cv2.flip(pi,1)
        img = Image.fromarray(pic)
        ima = ImageTk.PhotoImage(img)
        self.ImageMain.configure(image = ima)
        self.ImageMain.image = ima
        self.ImageMain.after(10,self.show_picture)

    def show_recv(self,frame):
        pi = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pic =  cv2.flip(pi,1)
        img = Image.fromarray(pic)
        ima = ImageTk.PhotoImage(img)
        self.ImageRecv.configure(image = ima)
        self.ImageRecv.image = ima


    def make_call(self):
       ip_address = self.ip_enter.get()
       port =int(self.port_enter.get())
       ip = (ip_address,port)
       self.server.Local_Server_outgoing.connect(ip)
       print(ip)
       check = self.server.Local_Server_outgoing.recv(1024)
       if check == b'alpha':
              self.lift_call(self.server.Local_Server_outgoing)

    def end_call(self,sock):
            ind = self.server.Incoming_request_socket_array.index(sock)
            self.m3nu.delete(self.Incoming_request_address_array[ind][0])
            self.server.Incoming_request_socket_array.pop(ind)
            self.server.Incoming_request_address_array.pop(ind)
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()

    def send(self,sock,data):
        sock.sendall(pickle.dumps(data))


    def recived(self,sock,buffer):
        ser_data = buffer
        packet = sock.recv(4096)
        ser_data += packet
        try:
           data = pickle.loads(ser_data)
        except:
           return(self.recived(sock,ser_data))
        else:
            return(pickle.loads(ser_data))


    def cascade(self):
        if self.para == self.Incoming_request_address_array :
            pass

        elif self.para != self.Incoming_request_address_array :
            a = len(self.para)
            b = len(self.Incoming_request_address_array)
            if b > a:
                for i in range(a,b):
                      self.m3nu.add_command(label = self.Incoming_request_address_array[i][0], command = self.lift_call(self.Incoming_request_address_array[i][0]))
            elif  a > b :
                       sel.para =  self.Incoming_request_address_array


    def lift_call(self,sock):
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                        send = executor.submit(sock.sendall,data)
                        rec_v = executor.submit(seck.recv,1024)
                        sn = send.result()
                        rc = rec_v.result()
                        return rc

            except socket.timeout :
                error_indicator = "call timed out"


if __name__ == '__main__':
             cli = server("local")
             cli.create_server(("",80),("",4000))
             avi = Aud_Vid("sound and sight")
             app = GUI(cli,avi)
             app.Application_Window.mainloop()