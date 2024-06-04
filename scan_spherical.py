#!/usr/bin/env python
# %*****************************************************************************************#
#  This Program moves the Gantry in a portion of a sphere around the camera.
#  For this the camera parameters should be defined in parameters_sphere.txt file.
#  The camera location in tank is represented by r_c
#  and is measured in mm.
#
#  Coordinate system definition is defined in gantry_spherical_scan.py.
# %*******************************************************************************************

# from datetime import datetime
import gantrycontrol as gc
from gantry_spherical_scan import camera
from gantry_spherical_scan import get_gantry_settings
import pgcamera2 as pg
import time
import subprocess
import numpy as np  # type: ignore
import argparse
import sys
import matplotlib.pyplot as plt

deg2rad = np.pi / 180.0
rad2deg = 180.0 / np.pi


# loading parameters for the scan from parameters_sphere.txt file
class Parameters:
    """
    Default paramters are:
    Nscan     = 200
    Rscan     = 450.0 # mm
    campos    = [800.0, 650.0, -600.0] #mm
    camfacing = [0.0, -1.0, 0.0]
    phimin    = -80.0 * deg2rad
    phimax    = 80.0 * deg2rad
    thetamin  = 20.0 * deg2rad
    thetamax  = 85.0 * deg2rad
    """

    def __init__(self, filename="parameters_sphere.txt"):
        self.Nscan = 200
        self.Rscan = 450.0  # cm
        self.campos = [800.0, 650.0, -600.0]  # cm
        self.camfacing = [0.0, -1.0, 0.0]
        self.phimin = -70.0 * deg2rad
        self.phimax = 70.0 * deg2rad
        self.thetamin = 20.0 * deg2rad
        self.thetamax = 85.0 * deg2rad

        self.load_parameters(filename)
        self.print_parameters()

    def load_parameters(self, filename):
        try:
            f = open(filename, "r")
            for line in f:
                line_s = line.split()
                first_char = line_s[0][0]
                if (
                    first_char != "#"
                ):  # Adding capability to add comments. Lines starting with '#' in parameters.txt are skipped.
                    name = line_s[0]
                    if name == "campos":
                        val = line.split("=")[1].split("#")[0].split(",")
                        val = [float(i) for i in val]
                        self.campos = np.array(val)
                    if name == "camfacing":
                        val = line.split("=")[1].split("#")[0].split(",")
                        val = [float(i) for i in val]
                        self.camfacing = np.array(val)
                    elif name == "phimin":
                        val = line.split("=")[1].split("#")[0]
                        self.phimin = deg2rad * float(val)
                    elif name == "phimax":
                        val = line.split("=")[1].split("#")[0]
                        self.phimax = deg2rad * float(val)
                    elif name == "Nscan":
                        val = line.split("=")[1].split("#")[0]
                        self.Nscan = int(val)
                    elif name == "thetamin":
                        val = line.split("=")[1].split("#")[0]
                        self.thetamin = deg2rad * float(val)
                    elif name == "thetamax":
                        val = line.split("=")[1].split("#")[0]
                        self.thetamax = deg2rad * float(val)
                    elif name == "Rscan":
                        val = line.split("=")[1].split("#")[0]
                        self.Rscan = float(val)
                print(first_char)
            f.close()
        except FileNotFoundError:
            print("Oops! can't find " + filename)
        except ValueError:
            print("Oops!  Some parameter value isn't a number.")

    def print_parameters(self):
        print("Nscan    =", self.Nscan)
        print("Rscan    =", self.Rscan, "mm")
        print("campos   =", self.campos, "mm")
        print("camfacing=", self.camfacing)
        print("phimin   =", rad2deg * self.phimin, "deg")
        print("phimax   =", rad2deg * self.phimax, "deg")
        print("thetamin =", rad2deg * self.thetamin, "deg")
        print("thetamax =", rad2deg * self.thetamax, "deg")


def plot_scan(c1, gsets, tls, label):
    npgsets = np.array(gsets)
    GX = npgsets.T[0]
    GY = npgsets.T[1]
    GZ = npgsets.T[2]
    Gphi = npgsets.T[3]  # type: ignore
    Gtheta = npgsets.T[4]  # type: ignore
    nptls = np.array(tls)
    TX = nptls.T[0]
    TY = nptls.T[1]
    TZ = nptls.T[2]
    NX = nptls.T[3]
    NY = nptls.T[4]
    NZ = nptls.T[5]
    fig = plt.figure(figsize=(3, 3), dpi=100)
    ax = fig.add_subplot(projection="3d")
    ax.plot(GX, GY, GZ)
    ax.scatter(GX, GY, GZ, marker=".")
    ax.scatter(c1.rc[0], c1.rc[1], c1.rc[2], marker="o")
    ax.set_xlabel("xg (mm)")
    ax.set_ylabel("yg (mm)")
    ax.set_zlabel("zg (mm)")  # type: ignore
    ax.set_title("Gantry position")
    # plt.tight_layout()
    plt.savefig("gantrypos_" + label + ".png")
    fig = plt.figure(figsize=(3, 3), dpi=100)
    ax = fig.add_subplot(projection="3d")
    ax.quiver(GX + TX, GY + TY, GZ + TZ, NX, NY, NZ, length=50.0)
    ax.scatter(c1.rc[0], c1.rc[1], c1.rc[2], marker="o")
    ax.set_xlabel("xg+xt (mm)")
    ax.set_ylabel("yg+yt (mm)")
    ax.set_zlabel("zg+zt (mm)")  # type: ignore
    ax.set_title("Target position and pointing")
    # plt.tight_layout()
    plt.savefig("gantrypospnt_" + label + ".png")
    print("min Gx=", np.min(GX), " max Gx=", np.max(GX))
    print("min Gy=", np.min(GY), " max Gy=", np.max(GY))
    print("min Gz=", np.min(GZ), " max Gz=", np.max(GZ))


def main():
    parser = argparse.ArgumentParser(description="scan_spherical options")
    parser.add_argument(
        "-p", "--param_file", default="parameters_sphere.txt", help="Parameter file"
    )
    parser.add_argument(
        "--dryrun", help="Do dry run, printing scan locations only", action="store_true"
    )
    parser.add_argument("--no-dryrun", dest="dryrun", action="store_false")
    parser.set_defaults(dryrun=True)
    parser.add_argument(
        "-c",
        "--camera",
        default=[],
        help="Camera number(s) to take images",
        action="append",
        nargs="+",
    )
    parser.add_argument(
        "-l", "--label", default="", help="Label to include in image names", type=str
    )
    parser.add_argument(
        "--rayfin", default=True, help="Rayfin camera only", action="store_true"
    )
    parser.add_argument("--no-rayfin", dest="rayfin", action="store_false")
    parser.set_defaults(rayfin=False)

    args = parser.parse_args()
    print(args)
    param = Parameters(args.param_file)
    gantry = gc.gantrycontrol()
    cam = camera(param.campos, param.camfacing)
    scanpts = cam.get_scanpoints(
        param.Nscan,
        param.Rscan,
        param.phimin,
        param.phimax,
        param.thetamin,
        param.thetamax,
    )
    gsets, tls = get_gantry_settings(cam, scanpts)

    print("Rayfin=", args.rayfin)
    if args.rayfin is True:
        print("Taking photos with Rayfin")

    print("Dryrun=", args.dryrun)
    if args.dryrun is True:
        print("Dry Run")
        print("gsets=")
        print(gsets)
        print("tls=")
        print(tls)
        plot_scan(cam, gsets, tls, args.label)
        return 0

    pgc = pg.pgcamera2()
    gantry.locate_home_xyz()
    for n, gset in enumerate(gsets):
        print("move", n, "to", gset)
        curx, cury, curz, curphi, curtheta = gset
        curphi *= rad2deg
        curtheta *= -rad2deg

        gantry.move("DM", "DM", curz)
        gantry.move(curx, cury, "DM", curphi, curtheta, 1000, 1000, 1000, 200, 200)
        time.sleep(1)

        # capturing image(s) here
        if args.rayfin is True:
            capture_command = [
                "ssh",
                "jamieson@hyperk.uwinnipeg.ca",
                "python /home/jamieson/HyperK_Summer_Photogrammetry/RayfinRelated/RayfinTCP_takepicture.py -i 192.168.0.102 -l 192.168.0.100 -p 8888",
            ]
            print(capture_command)
            capture = subprocess.run(  
                capture_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            time.sleep(5)

        else:
            for icam in args.camera[0]:
                label = (
                    str(n) + "pch" + icam + "_" + args.label + "_z" + str(round(curz, 1)) + "_y" + str(round(cury, 1)) + "_x" + str(round(curx, 1))
                )
                print(label)
                pgc.capture_image(int(icam), dir="", label=label, append_date=False)

    print("Done")


if __name__ == "__main__":
    sys.exit(main())
