#!/usr/bin/env python


# Program to move in x
# edit number_of_moves to change number of times it moves
# edit move_x_in_mm to change the distance moved
# edit delay_in_seconds to change how long to wait between moves
number_of_moves = 14
move_x_in_mm = 50.0
delay_in_seconds = 30


import gantrycontrol as gc
import time
import math
import subprocess
import numpy as np
import math
gantry = gc.gantrycontrol()

#Move desired axis(x,y,z) by desired mm
for i in range(number_of_moves):
  gantry.print_cur_pos_mm()
  print('moving',move_x_in_mm,'mm in x')
  gantry.move_rel(move_x_in_mm)
  print('sleeping',delay_in_seconds,'seconds after move',i)
  time.sleep( delay_in_seconds )

print('Done moves')


