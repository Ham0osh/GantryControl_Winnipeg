#!/usr/bin/env python
######## Program to move x,y,z axes by desired mm. ###########
######## Just answer the questions the program asks        ###########

import gantrycontrol as gc
import time
import math
import subprocess
import numpy as np
import math
gantry = gc.gantrycontrol()

#Move desired axis(x,y,z) by desired mm
run=True
while run:
  gantry.print_cur_pos_mm()
  axis=input("Which axis do you want to move(x,y,z) ? \n")
  value=float(input("By how much(mm) do you want to move "+axis+ " axis? \n"))
  if axis.lower()=='x':
    gantry.move_rel(value)
  elif axis.lower()=='y':
    gantry.move_rel(0,value)
  elif axis.lower()=='z':
    gantry.move_rel(0,0,value)

  done=input("Are you done (Y/N)? \n")
  if done.lower()=="y":  
    run=False
