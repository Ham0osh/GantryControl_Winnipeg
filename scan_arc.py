# *************************************************************************************************#
#  This Program moves the Gantry in an arc around the camera. For this the camera parameters      #
#  Should be defined in parameters.txt file. The camera location in tank is represented by r_c    #
#  and is measured in mm. In Parameters the Phi angle has zero on -Y axis.                        #
# *************************************************************************************************#

# Arc scan
#        -----------
#        |         |
#        |        /|-90 degree(phi)  -> 0
#        |       / |
#        |(+X)  |  |
#        | |    |<-|Camera -> 90
#        | |    \  |
#        | v     \ |
#        |        \| 90 degree(phi) -> 180
#        |         |
#        | <--(-Y) |
#        -----------
# Location of limit switch is -ve direction for move command.

from datetime import datetime
import gantrycontrol as gc
import pgcamera2 as pg
import time
import math
import subprocess
import numpy as np


# loading parameters for the scan from parameters.txt file
class Parameters:
    def __init__(
        self, filename="parameters.txt", offset=-90
    ):  # Default offset is -90 so that Phi angle has zero at -Y axis(Towards limit switch in Y axis).
        self.load_parameters(filename, offset)
        self.calculate_parameters()

    # 		self.print_parameters()

    def load_parameters(self, filename, offset):
        try:
            f = open(filename, "r")
            for line in f:
                line_s = line.split()
                first_char = line_s[0][0]
                if (
                    first_char != "#"
                ):  # Adding capability to add comments. Lines starting with '#' in parameters.txt are skipped.
                    name = line_s[0]
                    if name == "r_c":
                        val = line.split("=")[1].split("#")[0].split(",")
                        val = [float(i) for i in val]
                        self.r_c = np.array(val)
                    elif name == "phi_init":
                        val = line.split("=")[1].split("#")[0]
                        self.phi_min = math.radians(float(val) + offset)
                    elif name == "phi_final":
                        val = line.split("=")[1].split("#")[0]
                        self.phi_max = math.radians(float(val) + offset)
                    elif name == "N_phi":
                        val = line.split("=")[1].split("#")[0]
                        self.nphi = int(val)
                    elif name == "z_init":
                        val = line.split("=")[1].split("#")[0]
                        self.z_min = float(val)
                    elif name == "z_final":
                        val = line.split("=")[1].split("#")[0]
                        self.z_max = float(val)
                    elif name == "N_z":
                        val = line.split("=")[1].split("#")[0]
                        self.nz = int(val)
                    elif name == "scan_rad":
                        val = line.split("=")[1].split("#")[0]
                        self.r = float(val)
                print(first_char)
            f.close()
        except FileNotFoundError:
            print("Oops! can't find " + filename)
        except ValueError:
            print("Oops!  Some parameter value isn't a number.")

    def calculate_parameters(self):
        # Calculating the length of z step based on number of vertical stops.
        if self.nz == 1:
            self.z_step = 0
        else:
            self.z_step = (self.z_max - self.z_min) / (
                self.nz - 1
            )  # Number of divisions(edges) = no. of vertex(stops)-1

        if self.nphi == 1:
            self.phi_step = 0
        else:
            self.phi_step = (self.phi_max - self.phi_min) / (
                self.nphi - 1
            )  # Number of divisions(edges) = no. of vertex(stops)-1

    def print_parameters(self):
        print("r_c = ", self.r_c)
        print("phi_min = ", self.phi_min)
        print("phi_max = ", self.phi_max)
        print("N_phi = ", self.nphi)
        print("z_min = ", self.z_min)
        print("z_max = ", self.z_max)
        print("N_z = ", self.nz)
        print("r = ", self.r)


param = Parameters()

gantry = gc.gantrycontrol()

# zero the gantry; Moves the gantry to home(where all limit switches are)
gantry.locate_home_xyz()

# scan in circle
# Copying the parameter values into 'nicer' variable names
cur_phi = param.phi_min
zmin = param.z_min
zstep = param.z_step
r_c = param.r_c
phistep = param.phi_step


n = 1  # For keeping track of which z height we are in. For the purpose of assigning filename to images.
f_time = open("time_per_pos", "w")
for i in range(param.nz):
    # Moving Gantry here
    curz = zmin + zstep * i
    # 	_,_,curz,_,_ = gantry.unconvert( 1, 1, curz, 1, 1)
    gantry.move("DM", "DM", curz)
    for j in range(param.nphi):
        t1 = datetime.now()  # initial time
        print("Picture no: ", n)
        # print('cur t = ',t)
        r = param.r * np.array([math.cos(cur_phi), math.sin(cur_phi)])
        r_t = r_c + r
        print("current angle =", cur_phi)

        # Calculating Angle to make pattern tangent to the arc
        phi_prime = math.atan2(r[1], r[0]) + math.pi
        phi_t = math.degrees(
            phi_prime - math.pi / 2 - math.pi
        )  # Angle to make pattern tangent to the arc
        print("phi_t= ", phi_t)
        print("rx, ry = ", r[0], " ", r[1])
        print("phi_prime = ", phi_prime)

        gantry.move(r_t[0], r_t[1], "DM", phi_t, 0, 1000, 1000, 100, 100)
        time.sleep(1)
        cur_phi = cur_phi + phistep

        # capturing image here
        label = (
            str(n)
            + "_pch4air1_z"
            + str(round(curz, 1))
            + "_y"
            + str(round(r_t[1], 1))
            + "_x"
            + str(round(r_t[0], 1))
        )
        print(label)
        pgc = pg.pgcamera2()
        pgc.capture_image(4, dir="", label=label, append_date=False)

        label = (
            str(n) + "_pch7air1_z" + str(round(curz, 1)) + "_y" + str(round(cury, 1))
        )
        print(label)
        pgc.capture_image(7, dir="", label=label, append_date=False)

        capture_command = [
            "ssh",
            "jamieson@hyperk.uwinnipeg.ca",
            "python /home/jamieson/HyperK_Summer_Photogrammetry/RayfinRelated/RayfinTCP_takepicture.py -i 192.168.0.102 -l 192.168.0.100 -p 8888",
        ]
        print(capture_command)
        capture = subprocess.run(
            capture_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10
        )

        # Writing time taken to capture image per position.
        t2 = datetime.now()  # final time
        delta_t = (t2 - t1).total_seconds()
        print("time taken = ", delta_t)
        f_time.write(str(delta_t) + ", ")  # Write the time taken per pose.

    # flip sign of phi step to step back!
    phistep = -phistep
    cur_phi = cur_phi + phistep
    n += 1

# gantry.move("DM","DM","DM",0) #"DM" means don't move
print("Done scan")
f_time.close()  # close the file
del gantry
