#!/usr/bin/env python3

import sys
import argparse
import pgcamera2 as pg
import time

def main():
    parser = argparse.ArgumentParser(description='Image capture options')
    parser.add_argument('--nimages',default=1, help='Number of images (-1=non stop)', type=int)
    parser.add_argument('--timesep',default=1, help='Time between images (sec)', type=int)
    parser.add_argument('--appenddate',default=True, help='Append date to images?', type=bool)
    parser.add_argument('--dir',default='.',help='Directory to place images',type=str )
    parser.add_argument('--imglabel',default='img',help='Label to add to image',type=str )
    parser.add_argument('--buildcamfile',default=False,help='Build pgcamera_cameras.txt',type=bool )
    
    args = parser.parse_args()
    print(args)
    print('nimages=',args.nimages)
    print('timesep=',args.timesep)
    print('appenddate=',args.appenddate)
    print('dir=',args.dir)
    print('imglabel=',args.imglabel)
    print('buildcamfile=',args.buildcamfile)
    if args.buildcamfile:
        pgc = pg.pgcamera( buildcamerafile=True)
                        
    nimg = 0
    while True:
        pgc = pg.pgcamera2( )
        #print(pgc.camvitals)
        pg.print_camera_list( pgc.camvitals )
        for iser, icam, iaddr, iname in pgc.camvitals:
            pgc.capture_image( icam,  dir=args.dir, label=args.imglabel, append_date=args.appenddate )

        del pgc
        nimg = nimg + 1
        if args.nimages != -1 and nimg >= args.nimages:
            break;
        print('Waiting for',args.timesep,'seconds')
        time.sleep( args.timesep )
        
    print('Done collecting ', nimg,'images!')
        
if __name__ == "__main__":
    sys.exit(main())

