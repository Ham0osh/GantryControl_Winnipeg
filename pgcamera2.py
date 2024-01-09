'''
pgcamera2 is a python module to handle multiple cameras using gphoto2

Blair Jamieson
Nov. 2022
'''

import subprocess
import time

# Global blob of info
class pgcamera2:
    def __init__( self, camerafile='pgcamera_cameras.txt', buildcamerafile=False ):
        '''
        Setup camera control object to keep track of all
        cameras available, or just use ones in a list in a textfile.

        If buildcamerafile is True then the list_of_cameras_file
        is overwritten with the list of cameras found.

        If buildcamerafile is False then try to find all the
        cameras in the file.

        setcamno is the camera number to use from startup
        '''
        if buildcamerafile:
            self.camvitals = build_camera_file( camerafile )
        else:
            self.camvitals = read_camera_file( camerafile )

    def capture_image(self, cam_no,  dir='', label='img', append_date=True ):
        '''
        Takes a photo from camera cam_no and saves it as filename:
        'dir/c<num>_'+label[+date].jpg'

        Stores the camera settings in:
        'dir/c<unm>_'+label[+date].txt'
        '''
        cam_no = str(cam_no)
        idx = camvitals_index_from_camno( self.camvitals, cam_no )
        if idx < 0:
            print('capture_image camera ',cam_no,' not found')
            return
        imgname = dir+'/'
        if dir == '':
            imgname = '';
        imgname = imgname + 'c' + str(cam_no) + '_' + label
        if append_date:
            imgname = imgname + time.strftime('%Y%m%d-%H:%M:%S%Z')
        metaname = imgname + '.txt'
        imgname = imgname + '.jpg'
        command = ['gphoto2',
                   '--port='+self.camvitals[idx][2],
                   '--wait-event=4s',
                   '--capture-image-and-download',
                   '--filename='+imgname ]
        print(command)
        result = subprocess.run( command, capture_output=True, text=True )
        if result.stderr != '':  # check if there was an error
            print(result.stderr)
            self.camvitals = reset_camera_camvital_idx( self.camvitals, idx )
            # try the capture again
            command[3] = 'port='+self.camvitals[idx][2]
            print(command)
            result = subprocess.run( command, capture_output=True, text=True )
            if result.stderr != '':
                print(result.stderr, ' giving up!')
        #capture_abilities( self.camvitals[idx][2], metaname )


# Helper functions outsidet he class
def capture_abilities( port, metaname ):
        '''
        talk to camera at usbport 'port' to get its settings
        outfilename: textfile name into which the
        settings will be stored.

        Saves the camera settings, aka abilities into outfilename.
        Ignore generic unamed properties.
        '''
        try:
            f = open( metaname,'w')

            command = ['gphoto2',
                       '--port='+port,
                       '--summary']
            print(command)
            result = subprocess.run( command, capture_output=True, text=True )
            if result.stderr != '':
                print('capture_abilities(',port,',',metaname,') failed')
                f.close()
            settings_list = result.stdout.splitlines()

            # print first few lines as is
            for settings in settings_list[:5]:
                f.write(settings+'\n')
            for settings in settings_list[17:]:
                setlist = settings.split('(')
                setname = setlist[0].strip(': ()')
                setlist = settings.split(' ')
                setvalue = setlist[-1].strip(' ()')
                # skip generic unamed properties
                if setname.split(' ')[0] != 'Property' and setname != '':
                    f.write(setname+', value: '+setvalue+'\n')

            f.close()
        except:
            print('capture_abilities error file:',metaname,' not complete.')





def reset_camera_camvital_idx( camvitalold, idx ):
    '''
    Power cycle the camera at index idx, and rebuild the camvitals list
    with a new USB port number when it comes back.
    Returns the new camvitals list.
    '''
    print('reset_camera_camvital_idx to implemented')
    return camvitalold


def camvitals_index_from_serno( camvitals, serno ):
    '''
    Return the index into camvitals of the camera with serno.
    Returns -1 if it is not found.
    '''
    for idx, vital in enumerate(camvitals):
        if vital[0] == serno:
            return idx
    return -1

def camvitals_index_from_camno( camvitals, camno ):
    '''
    Return the index into camvitals of the camera with camera number.
    Returns -1 if it is not found.
    '''
    for idx, vital in enumerate(camvitals):
        if vital[1] == camno:
            return idx
    return -1


def get_camera_ports():
    '''
    Return the list of current port numbers with cameras connected.

    Returns the list:
    camports = [ [ser_no, port, cam_type], ... ]
    '''
    command = ['gphoto2','--auto-detect' ]
    result = subprocess.run( command, capture_output=True, text=True )
    lines = result.stdout.splitlines()
    camports = []
    #print('get_camera_ports result=',result)
    for line in lines:  
        #print('line=',line)
        words = line.split(' ')
        if words[0] != 'Sony':
            continue
        words = line.split(':')
        camname = words[0][:-6].strip(' ')
        camport = 'usb:'+words[1].strip(' ')
        serno = get_camera_serialno( camport )
        camports.append( [serno, camport, camname] )
    return camports

def get_camera_serialno( usbport ):
     '''
     Given a port string of the form usb:XXX,YYYY in usbport, use
     gphoto2 to get the serial number if a camera is found, or return
     '-1'
     '''
     command = ['gphoto2','--port='+usbport,'--wait-event=3s','--get-config=serialnumber']
     result = subprocess.run( command, capture_output=True, text=True )
     lines = result.stdout.splitlines()
     serno = "-1"
     for line in lines:
         words = line.split(' ')
         if words[0] == 'Current:':
             serno = words[1].strip(' ')
     print('usbport=',usbport,' serno=',serno)
     return serno

def build_camera_file( camerafile = 'pgcamera_cameras.txt' ):
     '''
     Return the list of camera vitals, and at the same time
     write a camera number and serial number to camerafile.

     camvitals = [ [ser_no, cam_no, port, cam_type ], ... ]
     '''
     camports = get_camera_ports()
     # sort by serial number and assign camera numbers
     sorted( camports, key=lambda x : x[0] )
     camvitals = []
     f = open( camerafile, 'w' )
     for i, camport in enumerate( camports ):
         camvitals.append( [camport[0], str(i+1), camport[1], camport[2] ] )
         f.write( str(i+1)+' '+camport[0]+'\n' )
     f.close()
     return camvitals


def read_camera_file( fname ):
     '''
     Looks for file fname which holds the mapping between serial number
     and camera number that can be written by the __init__ function.

     Note that since the usb port numbers can change, those aren't
     stored, but are refound each time.

     Returns camvitals for cameras from file that are currently connected.
     '''
     camports = get_camera_ports()
     camvitals = []
     try:
         f=open(fname,'r')
         lines = f.readlines()
         for line in lines:
            curcam, curserno = line.split(' ')
            curserno = curserno.strip('\n')
            #print('search for curcam=',curcam,' curserno=',curserno)
            #print(' in camports=',camports)
            for camport in camports:
                #print('... try camport=',camport,' serno=',camport[0])
                if camport[0] == curserno:
                    camvitals.append( [camport[0], curcam, camport[1], camport[2] ] )
                    break
         f.close()
     except:
         print('read_camera_file(',fname,') failed')
     return camvitals


def print_camera_list( camvitals ):
     '''
     Print out in a nice way the camera info that is in a camvitals list of lists.
     '''
     for vital in camvitals:
         print('Camera',vital[1],': Serial number:',vital[0],' Address:',vital[2],' Type:',vital[3])


