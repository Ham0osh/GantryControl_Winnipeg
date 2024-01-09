import sys
import string
import gclib
import time


class gantrycontrol:
  """
  gantrycontrol is a class to control the gantry motion in 0RC39.

  It assumes the last saved position in 'fname' passed to the class is correct.
  If it isn't you can call

  Usage:

  > import gantrylib as gl            # import the code
  > gantry = gl.gantrycontrol()       # build the gantry control instance
  > gantry.print_position()           # print current position
  > gantry.print_cur_pos_mm()         # Print current position in mm units
  > gantry.print_cur_pos()            # Print current position in counts units
  > gantry.get_cur_pos_mm()           # returns current position in mm
  > gantry.get_cur_pos()              # returns current position in counts
  > gantry.move( 1000 )               # move the gantry in x by 1000 mm from the origin
  > gantry.move( "DM",1000 )            # move the gantry in y by 1000 mm from the origin. "DM" in first place is necessary. Means don't move this axis.
                                      #If you use 0 instead of "DM" it will go to absolute position 0.
  > gantry.move( "DM","DM",1000 )         # move the gantry in z by 1000 mm from the origin.
  > gantry.move( "DM","DM","DM",1000 )      # move the gantry in theta by 1000 mm from the origin.
  > gantry.move( "DM","DM","DM","DM",1000 )   # move the gantry in phi by 1000 mm from the origin.
  > gantry.move( 10,20,30,40,50,1,2,3,4,5 ) # move x axis 10 mm with speed 1 cts/s, y axis 20 mm with speed 2 cts/s...
  > gantry.move_rel( 1000 )           # move the gantry in x by 1000 steps from the current position
  > gantry.move_rel( 0, 1000 )     # move the gantry in y by 1000 steps from the current position
  > gantry.move_rel( 0, 0, 1000 )     # move the gantry in z by 1000 steps from the current position
  > gantry.move_rel( 0, 0, 0,1000 )   # move the gantry in theta by 1000 steps from the current position
  > gantry.move_rel( 0, 0, 0,0,1000 ) # move the gantry in phi by 1000 steps from the current position
  > gantry.move_rel( 1, 2, 3,4,5,2,3,4,5,6 ) # move x axis 1 count with speed 2counts/s, axis y 2 counts with speed 2counts/s...
  > gantry.move_rel_mm(0,0,1000)      # moves z axis 1000 mm from current position. Same format as gantry.move_rel but unit is mm.
  > gantry.locate_home_xyz()          # jog the gantry to home (0,0,0)
  > del gantry                        # done using gantry, delete object (closes connections)
  """

  def __init__(self, fname='galil_last_position.txt'):
    self.g = gclib.py() #make an instance of the gclib python class
    self.c = self.g.GCommand #alias the command callable
    self.file_galilpos = fname

    print('gclib version:', self.g.GVersion())
    self.g.GOpen('192.168.42.10 -s ALL')
    print( self.g.GInfo() )
    self.load_position( ) # assume we are at last saved position

    print('Enable motors')
    self.c('SH') #Enable the motor

    print('Set smoothing on theta,phi axes')
    self.c('KS ,,,50,50')
    self.c('AC ,,,2048,1024')
    print(' done.')


  def __del__(self):
    '''
    Destructor saves position and closes connection
    '''
    self.g.GClose()

  #Get the maximum software limit on x,y,z axis in counts
  def get_max(self):
    res = self.c('FL ?,?,?')
    max_x,max_y,max_z = res.split(',')
    max_x = float(max_x)
    max_y = float(max_y)
    max_z = float(max_z)

    return max_x,max_y,max_z

  #move the gantry to centre of the tank in x,y,z.
  def move_to_centre(self):
    m_x,m_y,m_z = self.get_max()
    #Getting units in mm
    m_x,m_y,m_z,a,b=self.unconvert(m_x,m_y,m_z,0,0) # a,b are gibberish
    self.move(m_x/2,m_y/2,m_z/2)

  def print_position(self,message='Positon: '):
    '''
      print position of gantry
    '''
    print( message + self.c('PA ?,?,?,?,?') )

  def save_position(self):
    '''
    Read the current position from the galil and save it to file.
    '''
    res = self.c('PA ?,?,?,?,?')
    print(self.file_galilpos)
    f = open(self.file_galilpos,'w')
    f.write(res)
    f.close()
    print('wrote (x,y,z,phi,theta) to galil_last_position.txt: ',res)

  def load_position(self):
    '''
    Load position from file
    '''
    f = open(self.file_galilpos,'r')
    res = f.readline()
    command = 'DP '+res
    print('Loading position with command =',command)
    self.c(command)


  def locate_home_xyz(self):
    '''
      Jogs the gantry until it hits the limit switches.
      Defines that as 0,0,0 in xyz
      Writes the position to file
    '''
    try:
      self.print_position('before homing: ')
      '''
      Checking limit switch status _LRA variable contains limit switch status of reverse limit switch in axis  A.
      If the limit switch is already activated  that axis is already at home so we don't want to move it.
      '''

      RLA_status = float(self.c('MG _LRA'))==1.0 #1 means limit switch not activated
      RLB_status = float(self.c('MG _LRB'))==1.0
      RLC_status = float(self.c('MG _LRC'))==1.0
      print('abc status = ',RLA_status,RLB_status , RLC_status )
      x_speed = -1000 if RLA_status else 0
      y_speed = -1000 if RLB_status else 0
      z_speed = -1000 if RLC_status else 0
      print('speed = ',x_speed, y_speed, z_speed)
      command = 'JG %g,%g,%g,%g,%g'% (x_speed, y_speed, z_speed, 0, 0)
      self.c(command)
      axes = ''
      axes = 'A' if RLA_status else axes
      axes = axes+'B' if RLB_status else axes
      axes = axes+'C' if RLC_status else axes
      print('axes to stop = '+ axes)
      if len(axes)>0:
        command = 'BG'+axes
        self.c(command) # only BG the axes that have speed otherwise the value of _BGX for X axis will stay 1.

      self.g.GMotionComplete('ABCDE')
      time.sleep(1)
      self.c('DP 0,0,0')
      self.print_position('after homing: ')
      self.save_position()
    except:
      print('Homing failed.  Disabling motor')
      self.c('ST')
      self.c('MO')
      self.c('TE')

  def set_theta_phi_origin(self):
    self.c('DP ,,,0,0')
    self.save_position()

  #converts from mm to counts
  #Conversion factors obtained from calibration.
  def convert(self,x,y,z,phi,theta):
    x=round(x/0.01113)
    y=round(y/0.009382)
    z=round(z/0.009355)
    phi=round(phi/0.0226)
    theta=round(theta/0.02259)
    
    return x,y,z,phi,theta

  # converts counts to mm
  def unconvert(self,curx,cury,curz,curphi,curtheta):
    x = 0.01113*curx
    y = 0.009382*cury
    z = 0.009355*curz
    phi = 0.0226*curphi
    theta = 0.02259*curtheta
    
    return x,y,z,phi,theta

  # returns current position in mm
  def get_cur_pos_mm(self):
    curx,cury,curz,curphi,curtheta = self.get_cur_pos()
    x,y,z,phi,theta = self.unconvert(curx,cury,curz,curphi,curtheta)
    return x,y,z,theta,phi

  # Prints current position in mm
  def print_cur_pos_mm(self):
    x,y,z,phi,theta = self.get_cur_pos_mm()
    print('current (x,y,z,phi,theta) (mm) =',x,y,z,theta,phi )

  # returns current position in counts
  def get_cur_pos(self):
    res = self.c('PA ?,?,?,?,?')
    curx,cury,curz,curphi,curtheta = res.split(',')
    curx = float(curx)
    cury = float(cury)
    curz = float(curz)
    curtheta = float(curtheta)
    curphi = float(curphi)
    return curx,cury,curz,curphi,curtheta

  #Prints current position in counts
  def print_cur_pos(self):
    curx,cury,curz,curphi,curtheta = self.get_cur_pos() 
    print('current (x,y,z,phi,theta) (counts)=',curx,cury,curz,curphi,curtheta )


  #Returns axes whose position is changed.
  #only used for for absolute move command(not relative)
  #Absolute move has issues when you begin axes whose position is not changed.
  #Probably better to only use relative move.
  def axes_to_begin(self,x,y,z,phi,theta):
    res = self.c('PA ?,?,?,?,?')
    curx,cury,curz,curphi,curtheta = res.split(',')
    curx = float(curx)
    cury = float(cury)
    curz = float(curz)
    curtheta = float(curtheta)
    curphi = float(curphi)

    axes=''
    axes='A' if (x!=curx) else axes
    axes=axes+'B' if (y!=cury) else axes
    axes=axes+'C' if (z!=curz) else axes
    axes=axes+'D' if (phi!=curphi) else axes
    axes=axes+'E' if (theta!=curtheta) else axes
    return axes


  #Absolute move. Origin is where limit switches are. Takes x,y,z position to move to in mm.
  def move(self,x="DM",y="DM",z="DM",phi="DM",theta="DM",spx=1000,spy=1000,spz=1000,spphi=250,sptheta=250):
    '''
    move to absolute position and angle
    x,y,z in mm
    theta,phi in degrees
    default value is set to "DM". "DM" means don't move that axis. Can't use zero because it would mean move to absolute position 0.
    '''
    try:
      #check if we don't want to move some axis
      curx,cury,curz,curtheta,curphi = self.get_cur_pos_mm()
      #"DP" means don't move that axis.
      if str(x).lower()=="dm":
        x=curx
        print("inside x")
      if str(y).lower()=="dm":
        y=cury
        print("inside y")
      if str(z).lower()=="dm":
        z=curz
        print("inside z")
      if str(theta).lower()=="dm":
        print("inside th")
        theta=curtheta
      if str(phi).lower()=="dm":
        print("inside ph")
        phi=curphi

      # converting mm to counts
      c_x,c_y,c_z,c_phi,c_theta = self.convert(x,y,z,phi,theta)

      #setting up speed
      command = 'SP %g,%g,%g,%g,%g'% (spx,spy,spz,spphi,sptheta)
      print('SPEED COMMAND : ',command)
      self.c( command )

      print('current speed', self.c('SP ?,?,?,?,?'))


      #Sending absolute move command
      command = 'PA %g,%g,%g,%g,%g'% (c_x,c_y,c_z,c_phi,c_theta)
      print('try running in move: ',command)
      self.c( command )


      #Only begin the axes whose Absolute position has changed
      axes = self.axes_to_begin(c_x,c_y,c_z,c_phi,c_theta) #This check is not necessary if someone doesn't set speed of some axis to 0 by accident.
      print('axes = '+axes)
      if len(axes)>0:
        self.c('BG'+axes) # Begin only if there is any axes to begin
        self.g.GMotionComplete('ABCDE') # check if the motion has completed
        self.print_cur_pos()
        self.save_position()

    except:
      print("error returned by the controller during move command")
      #will implement code to print the error returned by controller in future
      self.c('ST')
      self.c('MO')
      print(self.c('TE'))
      

  #move x(counts) relative to current position
  def move_rel(self,x=0,y=0,z=0,phi=0,theta=0,spx=1000,spy=1000,spz=1000,spphi=250,sptheta=250):
    '''
    move relative distance x,y,z,phi,theta from current location
    distances are in motor steps
    saves position to file after moving
    '''
    try:
      #setting up speed
      command = 'SP %g,%g,%g,%g,%g'% (spx,spy,spz,spphi,sptheta)
      self.c( command )

      self.print_cur_pos()

      command = 'PR %g,%g,%g,%g,%g'% (x,y,z,phi,theta)
      print('try running: ',command)
      self.c( command )
      
      #Controller gives an error if the limit switch is activated, even if we are not moving that axis
      #So specifying the axis to move would get rid of that problem
      axes="" # axes to move 
      if x!=0:
          axes=axes+"A"
      if y!=0:
          axes=axes+"B"
      if z!=0:
          axes=axes+"C"
      if phi!=0:
          axes=axes+"D"
      if theta!=0:
          axes=axes+"E"
     
      if len(axes)>0:  
        self.c('BG'+axes)
        self.g.GMotionComplete('ABCDE')
        time.sleep(1)

        self.print_cur_pos()
        self.save_position()

    except:
      print("error returned by the controller during relative move command")
      #will implement code to print the error returned by controller in future
      self.c('ST')
      self.c('MO')
      self.c('TE')
     

  # move x(mm) relative to current position
  def move_rel_mm(self,x=0,y=0,z=0,phi=0,theta=0,spx=1000,spy=1000,spz=1000,spphi=250,sptheta=250):
    self.print_cur_pos_mm()
    x,y,z,phi,theta = self.convert(x,y,z,phi,theta)
    self.move_rel(x,y,z,phi,theta,spx,spy,spz,spphi,sptheta)
    self.print_cur_pos_mm()
