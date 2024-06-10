#*************************************************************************************************#
#  This Program moves the Gantry in an arc around the camera. For this the camera parameters      #
#  Should be defined in parameters.txt file. The camera location in tank is represented by r_c    #
#  and is measured in mm. In Parameters the Phi angle has zero on -Y axis.                        #
#*************************************************************************************************#


from datetime import datetime
import gantrycontrol as gc
import pgcamera2 as pg

import time
import math
import subprocess
import numpy as np

#loading parameters for the scan from parameters.txt file
class Parameters:
	def __init__(self,filename="parameters_yz.txt"): 
		self.load_parameters(filename)
		self.calculate_parameters()
#		self.print_parameters()
		
	def load_parameters(self,filename):
		try:
			f=open(filename,"r")
			for line in f:
				line_s=line.split()
				first_char=line_s[0][0]
				if first_char != '#': #Adding capability to add comments. Lines starting with '#' in parameters.txt are skipped.
					name=line_s[0]
					if name=="y_init":
						val=line.split('=')[1].split('#')[0]
						self.y_min=float(val)
					elif name=="y_final":
						val=line.split('=')[1].split('#')[0]
						self.y_max=float(val)
					elif name=="N_y":
						val=line.split('=')[1].split('#')[0]
						self.ny = int(val)
					elif name=="z_init":
						val=line.split('=')[1].split('#')[0]
						self.z_min = float(val)
					elif name=="z_final":
						val=line.split('=')[1].split('#')[0]
						self.z_max = float(val)
					elif name=="N_z":
						val=line.split('=')[1].split('#')[0]
						self.nz = int(val)
				print(first_char)
			f.close()
		except FileNotFoundError:
			print("Oops! can't find "+filename)
		except ValueError:
			print("Oops!  Some parameter value isn't a number.")

	def calculate_parameters(self):
		#Calculating the length of z step based on number of vertical stops.
		if self.nz==1:
			self.z_step=0
		else:
			self.z_step = (self.z_max-self.z_min)/(self.nz-1) #Number of divisions(edges) = no. of vertex(stops)-1

		if self.ny==1:
			self.y_step=0
		else:
			self.y_step = (self.y_max-self.y_min)/(self.ny-1) #Number of divisions(edges) = no. of vertex(stops)-1

	def print_parameters(self):
		print("y_min = ", self.y_min)
		print("y_max = ", self.y_max)
		print("N_y = ", self.ny)
		print("z_min = ", self.z_min)
		print("z_max = ", self.z_max)
		print("N_z = ", self.nz)


param=Parameters()

gantry = gc.gantrycontrol()

# zero the gantry; Moves the gantry to home(where all limit switches are)
# please position gantry at starting point!
#gantry.locate_home_xyz()

# scan in circle
#Copying the parameter values into 'nicer' variable names
zmin=param.z_min
ymin=param.y_min
zstep=param.z_step
ystep=param.y_step

cury = ymin

n=1 #For keeping track of which z height we are in. For the purpose of assigning filename to images.
e=1 #Keeping track of error #.
f_time = open("time_per_pos", "w")
for i in range( param.nz ):
    #Moving Gantry here
    curz = zmin+zstep*i
    print('curz=',curz)
    #	_,_,curz,_,_ = gantry.unconvert( 1, 1, curz, 1, 1)
    gantry.move( "DM", "DM", curz )
    for j in range( param.ny ):
        t1 = datetime.now() #initial time
        print('Picture no: ',n)
        #print('cur t = ',t)
        cury += ystep
        print("z=",curz,' y =',cury)
        label = str(n)+'_pch7_air_r1c_z'+str(round(curz,1))+'_y'+str(round(cury,1))
        print(label)


        gantry.move( "DM", cury, curz,"DM","DM",1000,1000,1000,100,100)
        time.sleep(1)

        pgc=pg.pgcamera2()
        pgc.capture_image(7,dir='',label=label,append_date=False)

        label = str(n)+'_pch4_air_r1c_z'+str(round(curz,1))+'_y'+str(round(cury,1))
        print(label)
        pgc.capture_image(4,dir='',label=label,append_date=False)

        capture_command = ['gphoto2','--wait-event=3s','--capture-image-and-download','--filename='+str(label)+".jpg" ]
        print(capture_command)
        capture=subprocess.run( capture_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE )

        #capture_command = ['ssh','jamieson@hyperk.uwinnipeg.ca','python /home/jamieson/HyperK_Summer_Photogrammetry/RayfinRelated/RayfinTCP_takepicture.py -i 192.168.0.102 -l 192.168.0.100 -p 8888' ]
        #print(capture_command)
        #capture=subprocess.run( capture_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE )


        #print('interpreting capture...')
        #out=(capture.stdout).decode('UTF-8')
        #print(out[692:])
        #error=(capture.stderr).decode('UTF-8') #error returned by camera
        #if error!='':
        #    print("The error is = ",error)
        n=n+1
        print('n=',n)



	# flip sign of phi step to step back!
    print('flip sign of y step')
    ystep = -ystep
    time.sleep(1)
    n+=1

#gantry.move("DM","DM","DM",0) #"DM" means don't move
print('Done scan')
f_time.close() # close the file
del gantry
