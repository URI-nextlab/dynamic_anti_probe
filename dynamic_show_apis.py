import serial.tools.list_ports
import serial
import numpy as np
import matplotlib.pyplot as plt
import time
import socket
import sys
BUFFER_SIZE = 16384
TARGET_ADDR = ''
TARGET_PORT = 60000
TARGET = (TARGET_ADDR,TARGET_PORT)
plist = list(serial.tools.list_ports.comports())
folder = './data/'



win = np.hamming(448);
LPF = np.ones([60])
LPF = np.append(LPF,np.zeros([329]))
LPF = np.append(LPF,np.ones([59]))


class dynamic_show:
	ss = 0
	B = 36
	stop_thread = False
	abuffer_size = 0
	Averager_index = 0;
	data = np.zeros(448,dtype=np.uint32)
	shot = np.zeros(448,dtype=np.complex);
	Slice_Averager = 0
	enable_deconv = 0
	ff_std = 0;
	LPF_compensate = 0;
	LPF = 0;
	def __init__(self,abuffer_size):	
		self.ss = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.ss.bind(TARGET)
		self.Slice_Averager = np.zeros((abuffer_size,448),dtype=np.uint32)
		self.abuffer_size = abuffer_size
		self.enable_deconv = False
		std = np.loadtxt('pstd.txt');
		std = std - np.max(std)
		std = std / np.max(np.abs(std))
		self.ff_std = np.fft.fft(std,448)
		self.LPF = np.ones([self.B+1])
		self.LPF = np.append(self.LPF,np.zeros([448-self.B-self.B-1]))
		self.LPF = np.append(self.LPF,np.ones([self.B]))
		self.LPF_compensate = np.abs(np.fft.ifft(self.LPF))
		self.LPF_compensate = self.LPF_compensate / np.abs(self.LPF_compensate[0]);

	def socket_run(self):
		while True:
			if self.stop_thread == True:
				self.ss.close()
				print('closed!!!!!!!!!!!!!')
				break;
			else:
				self.ss.settimeout(1.0)
				try:
					data,addrRsv = self.ss.recvfrom(BUFFER_SIZE)
				except:
					pass
				else:
					data = np.frombuffer(data,dtype = np.uint32)
					self.Slice_Averager[self.Averager_index] = data.copy();
					self.Averager_index = self.Averager_index + 1;
					self.Averager_index = self.Averager_index % self.abuffer_size;

	def close_socket(self):
		self.stop_thread = True

	def get_data(self):
		display_data = np.sum(self.Slice_Averager,axis = 0)
		display_data = display_data / (416 * self.abuffer_size /10)	
		if self.enable_deconv == True:
			ff_d = np.fft.fft(display_data);
			ff = ff_d / self.ff_std;
			display_data = np.fft.ifft(ff * self.LPF);
			temp = np.abs(np.abs(display_data)-np.abs(display_data[0])*np.abs(self.LPF_compensate))
			return temp;
		else:
			return display_data;

	def shot_wave(self):
		data = self.get_data();
		self.shot = data.copy();


	def inc_bw(self):
		self.B = self.B + 1;
		if self.B > 223:
			self.B = 222;
		LPF = np.ones([self.B+1])
		LPF = np.append(LPF,np.zeros([448 - self.B - self.B -1]))
		LPF = np.append(LPF,np.ones([self.B]))
		self.LPF = LPF.copy();
		self.LPF_compensate = np.abs(np.fft.fft(LPF))
		self.LPF_compensate = self.LPF_compensate / np.abs(self.LPF_compensate[0]);
		print('BandWidth = '+ str(self.B * 19.5312))

	def dec_bw(self):
		self.B = self.B - 1;
		if self.B < 2:
			self.B = 2;
		LPF = np.ones([self.B+1])
		LPF = np.append(LPF,np.zeros([448 - self.B - self.B - 1]))
		LPF = np.append(LPF,np.ones([self.B]))	
		self.LPF = LPF.copy();
		self.LPF_compensate = np.abs(np.fft.fft(LPF))
		self.LPF_compensate = self.LPF_compensate / np.abs(self.LPF_compensate[0]);
		print('BandWidth = '+str(self.B * 19.5312))

	def get_shot(self):
		return self.shot;

	def t_deconv(self):
		self.enable_deconv = not self.enable_deconv; 

	def update_reference(self):
		display_data = np.sum(self.Slice_Averager,axis = 0)
		display_data = display_data / (416 * self.abuffer_size /10)
		self.ff_std = np.fft.fft(display_data,448)


	def save_data(self):
		display_data = np.sum(self.Slice_Averager,axis = 0)
		display_data = display_data / (416 * self.abuffer_size /10)
		name = input('Please input the name:\n')
		np.savetxt(name,display_data)
		print('Data saved to '+name+'.txt')

def show_available_uart():
	if len(plist) <= 0:
		print("No available uart!\n")
	else:
		print("Available PORT>>>")
		for i in range(len(plist)):
			plist_0 = list(plist[i])
			serialName = plist_0[0]
			serialFd = serial.Serial(serialName, 115200, timeout=60)
			print("\t",serialFd.name)

class Serial_Port:
	message = '';
	port = 0;
	def __init__(self,port,baud):
		self.port = serial.Serial(port,baud);
		if not self.port.isOpen():
			self.port.open()

	def send_data(self,data):
		number = self.port.write(data);
		return number;

	def read_data(self,counter = 1):
		while counter > 0:
			self.message=self.port.readline()
			counter = counter - 1;
		temp = self.message.decode("utf-8")
		return temp

	def read_package(self,buffer,N):
		temp = self.read_data();
		temp = temp.replace('\r\n','')
		while temp.isdigit():
			temp = self.read_data();
			temp = temp.replace('\r\n','')

		i = 0;
		while i < N:
			buffer[i] = int(self.port.readline());
			i = i + 1;



def single_plot(name,average_times):
	index,data = get_data(name,average_times);
	plt.plot(index,data,linewidth=0.8);
	plt.xlim([0,6.4]);
	plt.xlabel('T/ns')
	plt.ylabel('V/mV')
	plt.show()
	plt.draw()
