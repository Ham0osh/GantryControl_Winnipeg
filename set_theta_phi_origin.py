#!/usr/bin/env python
######## Program to set the origin for phi and theta axes. ###########
######## Just answer the questions the program asks        ###########

import gantrycontrol as gc
import time
import math
import subprocess
import numpy as np
import math
gantry = gc.gantrycontrol()

#Defining the origin for phi axis
phi_not_done = True
while phi_not_done:
	key=input("does the phi orientation look good, Y/N ? \n")
	if(key.lower()=='y'):
		phi_not_done=False
	elif(key.lower()=='n'):
		angle=float(input("what angle(degree) do you want to rotate phi by? \n"))
		gantry.move_rel(0,0,0,angle,0,1000,1000,1000,250,100)

print("Awesome! Let's fix theta now.")

#Defining the origin for theta axis
theta_not_done = True
while theta_not_done:
	key=input("does the theta orientation look good, Y/N ? \n")
	if(key.lower()=='y'):
		theta_not_done=False
	elif(key.lower()=='n'):
		angle=float(input("what angle(degree) do you want to rotate theta by? \n"))
		gantry.move_rel(0,0,0,0,angle,1000,1000,1000,250,100)

gantry.set_theta_phi_origin()

print("This should do it. Now the origin of theta and phi should be set as current position.")

del gantry
