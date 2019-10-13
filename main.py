
import dynamic_show_apis as apis
import numpy as np
import matplotlib.pyplot as plt
import time
import socket
import sys
import multiprocessing
import threading
name = 'temp'
flag = False
lflag = False
inst = apis.dynamic_show(200);
ymax = 0;

stop_thread = False
def on_key_press(event):
	global flag
	global lflag
	global ymax
	global stop_thread
	if event.key in 'Q':
		inst.close_socket()
		stop_thread = True;
	if event.key in 's':
		inst.save_data()
	if event.key in 'c':
		inst.shot_wave()
	if event.key in 't':
		lflag = not lflag;
		inst.t_deconv()
	if event.key in 'v':
		flag = not flag;
	if event.key in 'r':
		ymax = 0;
	if event.key in 'u':
		inst.update_reference()
	if event.key in '+':
		inst.inc_bw()
	if event.key in '-':
		inst.dec_bw()

def draw_run():
	global lflag
	global flag
	global stop_thread
	global ymax;
	print('started\n')
	fig = plt.figure();
	fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)
	fig.canvas.mpl_connect('key_press_event', on_key_press)
	plt.ion()
	index = np.arange(0,448)
	index = index * 0.0143;
	plt.draw()
	while True:
		if stop_thread == True:
			break;
		plt.clf()
	#	inst.socket_run();
		if lflag == False:
			plt.ylim([0,10])
		else:
			plt.ylim([0,ymax])
		plt.xlim([0,6.4]);
		plt.xlabel('T/ns')
		plt.ylabel('V/mV')
		data = inst.get_data();
		if flag:
			plt.plot(index,data,linewidth=0.8);
			plt.plot(index,inst.get_shot(),linewidth=0.8);
		else:
			plt.plot(index,data,linewidth=0.8);

		if lflag == True:
			temp = np.max(data);
			if temp > ymax:
				ymax = temp;
		plt.draw()
		plt.pause(0.01)

if __name__ == '__main__':
	ss_t = threading.Thread(target=inst.socket_run, args=())
	ss_t.setDaemon(True)
	ss_m = threading.Thread(target=draw_run, args=())
	ss_m.setDaemon(True)
	ss_t.start()
	ss_m.start()
	ss_t.join()
	ss_m.join()

