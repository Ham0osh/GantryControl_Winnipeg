import numpy as np  # type: ignore
import math

deg2rad = np.pi / 180.0
rad2deg = 180.0 / np.pi


# Default parameters class to be overwritten
class Parameters:
    """High level parameter class for each scan type."""

    def __init__(self, filename="parameters.txt"):
        self._filename = filename
        self._allowed_parameters = {}

    def load_parameters(self, filename, *args, **kwargs):
        pass

    def calculate_parameters(self):
        pass

    def print_parameters(self):
        return []

    def export_parameters(self, outfilename: str = 'tmp_parameters.txt'):
        lines = self.print_parameters()
        with open(outfilename, "r+") as savefile:
            # convert to string:
            _ = savefile.read()
            savefile.seek(0)
            for line in lines:
                savefile.write(line + '\n')
            savefile.truncate()


# loading parameters for the scan from parameters_sphere.txt file
class ParametersSphere(Parameters):
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
        self._allowed_parameters = [
            "campos",
            "camfacing",
            "phimin",
            "phimax",
            "thetamin",
            "thetamax",
            "Nscan",
            "Rscan",
        ]
        # Set defaults
        self.Nscan = 200
        self.Rscan = 450.0  # cm
        self.campos = [800.0, 650.0, -600.0]  # cm
        self.camfacing = [0.0, -1.0, 0.0]
        self.phimin = -70.0 * deg2rad
        self.phimax = 70.0 * deg2rad
        self.thetamin = 20.0 * deg2rad
        self.thetamax = 85.0 * deg2rad

        self.load_parameters(filename)
        # self.print_parameters()

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
                    if name not in self._allowed_parameters:
                        print(
                            "ValueError: Parameter {name} not a valid parameter entry for spherical scan. Continuing."
                        )
                        pass
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
        except FileNotFoundError as e:
            print("Oops! can't find " + filename)
            print(e)
        except ValueError as e:
            print("Oops!  Some parameter value isn't a number.")
            print(e)

    def print_parameters(self):
        print(l1 := f"Nscan    = {self.Nscan}")
        print(l2 := f"Rscan    = {self.Rscan} mm")
        print(l3 := f"campos   = {self.campos} mm")
        print(l4 := f"camfacing= {self.camfacing}")
        print(l5 := f"phimin   = {rad2deg * self.phimin} deg")
        print(l6 := f"phimax   = {rad2deg * self.phimax} deg")
        print(l7 := f"thetamin = {rad2deg * self.thetamin} deg")
        print(l8 := f"thetamax = {rad2deg * self.thetamax} deg")
        return [l1, l2, l3, l4, l5, l6, l7, l8]


# loading parameters for the scan from parameters_arc.txt file
class ParametersArc(Parameters):
    def __init__(
        self, filename="parameters.txt", offset=-90
    ):  # Default offset is -90 so that Phi angle has zero at -Y axis(Towards limit switch in Y axis).
        self._allowed_parameters = [
            "r_c",
            "phi_init",
            "phi_final",
            "N_phi",
            "z_init",
            "z_final",
            "N_z",
            "scan_rad",
        ]

        self.load_parameters(filename, offset)
        self.calculate_parameters()

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
                    if name not in self._allowed_parameters:
                        print(
                            "ValueError: Parameter {name} not a valid parameter entry for spherical scan. Continuing."
                        )
                        pass
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
        except FileNotFoundError as e:
            print("Oops! can't find " + filename)
            print(e)
        except ValueError:
            print("Oops!  Some parameter value isn't a number.")
            print(e)

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
        print(l1 := f"r_c =  {self.r_c}")
        print(l2 := f"phi_min = {self.phi_min}")
        print(l3 := f"phi_max = {self.phi_max}")
        print(l4 := f"N_phi = {self.nphi}")
        print(l5 := f"z_min = {self.z_min}")
        print(l6 := f"z_max = {self.z_max}")
        print(l7 := f"N_z = {self.nz}")
        print(l8 := f"r = {self.r}")
        return [l1, l2, l3, l4, l5, l6, l7, l8]
