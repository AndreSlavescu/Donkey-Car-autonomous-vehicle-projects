import os
import random
import json
import time
from io import BytesIO
import base64
import logging
import math

from PIL import Image
import numpy as np
from gym_donkeycar.core.sim_client import SDClient

import cv2


###########################################

class SimpleClient(SDClient):

    def __init__(self, address, poll_socket_sleep_time=0.01, verbose=False):
        super().__init__(*address, poll_socket_sleep_time=poll_socket_sleep_time)
        self.last_image = None
        self.car_loaded = False
        self.verbose = verbose
        self.wcCount=0
        self.cmdPos=0
        self.startTime=time.time()
        self.whiteCount = []
        self.prevWC = 0
        # self.cmds = [(225,0,1),(55,0.5,0.5),(15,0.5,0.6),(15,0.3,0.4),(225,0,1)]
        self.cmds = [(320,0,1),(20,-0.22,0.4),(35,0,0.4),(135,1,0.5),(70,0.7,0.5),(735,-0.007,1),(53,0.55,0.8),(40,-0.7,-0.4),(660,-0.05,1),(260,0.1,1)]
        # self.cmds = [(320,0,1),(20,-0.22,0.4),(35,0,0.4),(135,1,0.5),(70,0.7,0.5),(734,-0.007,1),(54,0.5,0.8),(55,-0.7,-0.25),(1,-0.5,1),(460,0,1)]

    def on_msg_recv(self, json_packet):
        if json_packet['msg_type'] == "need_car_config":
            self.send_config()

        if json_packet['msg_type'] == "car_loaded":
            self.send_config()
            self.car_loaded = True
        
        if json_packet['msg_type'] == "telemetry":
            imgString = json_packet["image"]
            image = Image.open(BytesIO(base64.b64decode(imgString)))
            # image.save("camera_a.png")
            # self.last_image = np.asarray(image)
            
            nowTime = time.time()

            # opencvImage = cv2.cvtColor(self.last_image, cv2.COLOR_RGB2BGR)
            opencvImage = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            self.last_image = opencvImage

            cv2.waitKey(1)
            # opencvImage = numpy.array(image)
            cv2.putText(opencvImage, "Time: "+str(nowTime-self.startTime), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255,255,255), 2)

            cv2.imshow("image_a",opencvImage)

            if self.verbose:
                print("img:", self.last_image.shape)

            # don't have to, but to clean up the print, delete the image string.
            del json_packet["image"]

            if "imageb" in json_packet:
                imgString = json_packet["imageb"]
                image = Image.open(BytesIO(base64.b64decode(imgString)))
                # image.save("camera_b.png")
                # np_img = np.asarray(image)
                opencvImage = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                # opencvImage = numpy.array(image)

                cv2.putText(opencvImage, "Time: "+str(nowTime-self.startTime), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255,255,255), 2)

                cv2.imshow("image_b",opencvImage)
                key = cv2.waitKey(1)
                if key == 27:
                    quit()
                # if self.verbose:
                #     print("imgb:", np_img.shape)

                # don't have to, but to clean up the print, delete the image string.
                del json_packet["imageb"]

            if "lidar" in json_packet:
                lidar = json_packet["lidar"]
                if lidar is not None:
                    if self.verbose:
                        print("lidar:", len(lidar), "pts")

                # don't have to, but to clean up the print, delete the lidar string.
                del json_packet["lidar"]

        if self.verbose:
            print("got:", json_packet)

    def send_config(self):
        '''
        send three config messages to setup car, racer, and camera
        '''
        racer_name = "Your Name"
        car_name = "Car"
        bio = "I race robots."
        country = "Neverland"
        guid = "some random constant string"

        # Racer info
        msg = {'msg_type': 'racer_info',
            'racer_name': racer_name,
            'car_name' : car_name,
            'bio' : bio,
            'country' : country,
            'guid' : guid }
        self.send_now(json.dumps(msg))
        time.sleep(0.2)
        
        # Car config
        # body_style = "donkey" | "bare" | "car01" choice of string
        # body_rgb  = (128, 128, 128) tuple of ints
        # car_name = "string less than 64 char"

        msg = '{ "msg_type" : "car_config", "body_style" : "car01", "body_r" : "255", "body_g" : "0", "body_b" : "255", "car_name" : "%s", "font_size" : "100" }' % (car_name)
        self.send_now(msg)

        # this sleep gives the car time to spawn. Once it's spawned, it's ready for the camera config.
        time.sleep(0.2)

        # Camera config
        # set any field to Zero to get the default camera setting.
        # this will position the camera right above the car, with max fisheye and wide fov
        # this also changes the img output to 255x255x1 ( actually 255x255x3 just all three channels have same value)
        # the offset_x moves camera left/right
        # the offset_y moves camera up/down
        # the offset_z moves camera forward/back
        # with fish_eye_x/y == 0.0 then you get no distortion
        # img_enc can be one of JPG|PNG|TGA        

        # msg = '{ "msg_type" : "cam_config", "fov" : "150", "fish_eye_x" : "1.0", "fish_eye_y" : "0", "img_w" : "640", "img_h" : "480", "img_d" : "1", "img_enc" : "JPG", "offset_x" : "0.0", "offset_y" : "1.0", "offset_z" : "0.0", "rot_x" : "90.0" }'
        # msg = '{ "msg_type" : "cam_config", "fov" : "0", "fish_eye_x" : "0", "fish_eye_y" : "0", "img_w" : "1280", "img_h" : "720", "img_d" : "1", "img_enc" : "JPG", "offset_x" : "0.0", "offset_y" : "0", "offset_z" : "0.0", "rot_x" : "0" }'
        # msg = '{ "msg_type" : "cam_config", "fov" : "0", "fish_eye_x" : "0", "fish_eye_y" : "0", "img_w" : "1280", "img_h" : "720", "img_d" : "3", "img_enc" : "JPG", "offset_x" : "0.0", "offset_y" : "0", "offset_z" : "0.0", "rot_x" : "0" }'
        # msg = '{ "msg_type" : "cam_config", "fov" : "80", "fish_eye_x" : "0", "fish_eye_y" : "0", "img_w" : "640", "img_h" : "480", "img_d" : "1", "img_enc" : "JPG", "offset_x" : "0.0", "offset_y" : "0", "offset_z" : "0.0", "rot_x" : "0" }'
        msg = '{ "msg_type" : "cam_config", "fov" : "0", "fish_eye_x" : "0", "fish_eye_y" : "0", "img_w" : "640", "img_h" : "480", "img_d" : "3", "img_enc" : "JPG", "offset_x" : "0.0", "offset_y" : "0", "offset_z" : "0.0", "rot_x" : "0" }'
        # msg = '{ "msg_type" : "cam_config", "fov" : "130", "fish_eye_x" : "0.0", "fish_eye_y" : "0", "img_w" : "640", "img_h" : "480", "img_d" : "3", "img_enc" : "JPG", "offset_x" : "0.0", "offset_y" : "3.0", "offset_z" : "2.0", "rot_x" : "90.0" }'

        self.send_now(msg)
        time.sleep(0.2)

        # Camera config B, for the second camera
        # set any field to Zero to get the default camera setting.
        # this will position the camera right above the car, with max fisheye and wide fov
        # this also changes the img output to 255x255x1 ( actually 255x255x3 just all three channels have same value)
        # the offset_x moves camera left/right
        # the offset_y moves camera up/down
        # the offset_z moves camera forward/back
        # with fish_eye_x/y == 0.0 then you get no distortion
        # img_enc can be one of JPG|PNG|TGA

        # msg = '{ "msg_type" : "cam_config_b", "fov" : "150", "fish_eye_x" : "1.0", "fish_eye_y" : "1.0", "img_w" : "255", "img_h" : "255", "img_d" : "1", "img_enc" : "JPG", "offset_x" : "3.0", "offset_y" : "3.0", "offset_z" : "0.0", "rot_x" : "90.0" }'
        # self.send_now(msg)
        time.sleep(0.2)

        # Lidar config
        # the offset_x moves camera left/right
        # the offset_y moves camera up/down
        # the offset_z moves camera forward/back
        # degPerSweepInc : as the ray sweeps around, how many degrees does it advance per sample (int)
        # degAngDown : what is the starting angle for the initial sweep compared to the forward vector
        # degAngDelta : what angle change between sweeps
        # numSweepsLevels : how many complete 360 sweeps (int)
        # maxRange : what it max distance we will register a hit
        # noise : what is the scalar on the perlin noise applied to point position
        # Here's some sample settings that similate a more sophisticated lidar:
        # msg = '{ "msg_type" : "lidar_config", "degPerSweepInc" : "2", "degAngDown" : "25", "degAngDelta" : "-1.0", "numSweepsLevels" : "25", "maxRange" : "50.0", "noise" : "0.2", "offset_x" : "0.0", "offset_y" : "1.0", "offset_z" : "1.0", "rot_x" : "0.0" }'
        # And here's some sample settings that similate a simple RpLidar A2 one level horizontal scan.

        # msg = '{ "msg_type" : "lidar_config", "degPerSweepInc" : "2", "degAngDown" : "0", "degAngDelta" : "-1.0", "numSweepsLevels" : "1", "maxRange" : "50.0", "noise" : "0.4", "offset_x" : "0.0", "offset_y" : "0.5", "offset_z" : "0.5", "rot_x" : "0.0" }'
        # self.send_now(msg)
        time.sleep(0.2)


    def send_controls(self, steering, throttle):
        msg = { "msg_type" : "control",
                "steering" : steering.__str__(),
                "throttle" : throttle.__str__(),
                "brake" : "0.0" }
        self.send(json.dumps(msg))

        # this sleep lets the SDClient thread poll our message and send it out.
        time.sleep(self.poll_socket_sleep_sec)

    def update(self):
    #     if self.cmdPos < len(self.cmds):
    #         (cmdCnt,st,th) = self.cmds[self.cmdPos]
    #         if cmdCnt>0:
    #             cmdCnt=cmdCnt-1.5
    #             self.cmds[self.cmdPos] = (cmdCnt,st,th)
    #         else:
    #             self.cmdPos = self.cmdPos+1
    #             if self.cmdPos < len(self.cmds):
    #                 (cmdCnt,st,th) = self.cmds[self.cmdPos]
    #                 cmdCnt=cmdCnt-1.5
    #                 self.cmds[self.cmdPos] = (cmdCnt,st,th)
    #             else:
    #                 #stop the car
    #                 st = 0
    #                 th = 0
        # else:
        #     #stop the car
        #     st = 0
        #     th = 0
        #     quit()
        th = 1
        st = 0
        img = self.last_image
        wc = 0
        try:   
            # crop_img = img[350:350+25, 0:0+639]
            # cv2.imshow("crop1", crop_img)
            crop_img = img[200:200+20, 0:0+639]
            # crop_img = img
            # cv2.imshow("crop2", crop_img)
            img = cv2.Canny(crop_img, 100, 150)
            # ret,img=cv2.threshold(img,133,255,cv2.THRESH_BINARY_INV)
        
            for i in range(5,15):
                x = 305-i*20
                img1 = img[0:20, x:x+20]
                wc = cv2.countNonZero(img1) 
                # cv2.imshow("img1", img1)
                # key = cv2.waitKey(1)
                
                if wc > 20:
                    img[0:20, x:x+20] = 255
                    # if i > 10:
                    #     st = 0.3
                    #     # th = th*0.5
                    # elif i < 5:
                    #     st = -0.3
                        # th = th*0.5
                    print("whiteCount", wc, x)
                    # self.whiteCount[self.wcCount] = wc
                    # self.wcCount = self.wcCount+1
                    wc = i
                    break

            if wc > 0:
                if wc < 5 or wc > 10:
                    th = 0.2
                    if wc < 5:
                        st = -0.7
                    elif wc > 10:
                        st = 0.7
                else:
                    th = 0.4
                    if wc > 5:
                        st = -0.3
                    elif wc < 10:
                        st = 0.3

            # if wc > 0:
            #     if wc < 10:
            #         st = 0.3
            #     elif wc > 5:
            #         st = -0.3
                # if self.prevWC > 0:
                #     if wc > (self.prevWC):
                #         st = 0.2
                #         th = th*0.1
                #         # th = th/abs(wc-self.prevWC)
                #     elif wc < (self.prevWC):
                #         st = -0.2   
                #         th = th*0.1
                #         # th = th/abs(wc-self.prevWC)             
                self.prevWC = wc
            #     print(self.wcCount, self.whiteCount[self.wcCount-1])
                # if self.wcCount > 1 and wc > (self.whiteCount[self.wcCount-2]+5):
                #     st = 0.5
                # elif self.wcCount > 1 and wc < (self.whiteCount[self.wcCount-2]+5):
                #     st = -0.5

            # for i in range(20):
            #     x = 320+i*15
            #     img1 = img[ 0:15, x:x+15]
            #     whiteCount = cv2.countNonZero(img1) 
            #     # cv2.imshow("img1", img1)
            #     # key = cv2.waitKey(1)
            #     print("whiteCount", whiteCount, x)
            #     if whiteCount > 20:
            #         img[0:15, x:x+15] = 255
            #         if i > 15:
            #             st = 0.3
            #             th = 0.3
            #         elif i < 5:
            #             st = -0.3
            #             th = 0.3            

            cv2.imshow("processed", img)
            key = cv2.waitKey(1)
        except Exception as e:
            print(e)
            pass    
        # just random steering now
        # st = 0 #random.random() * 5.0 - 1.0
        # th = 1
        self.send_controls(st, th)

    def update1(self):
        img = self.last_image
        st = 0
        th = 1
        try:   
            # crop_img = img[350:350+25, 0:0+639]
            # cv2.imshow("crop1", crop_img)
            crop_img = img[200:200+25, 0:0+639]
            # cv2.imshow("crop2", crop_img)
            img = cv2.Canny(crop_img, 100, 180)
            cv2.imshow("processed", img)
            key = cv2.waitKey(1)
        except:
            pass    
        self.send_controls(st, th)


###########################################
## Make some clients and have them connect with the simulator

def test_clients():
    logging.basicConfig(level=logging.INFO)

    # test params
    host = "localhost" # "trainmydonkey.com" for virtual racing server
    port = 9091
    num_clients = 1
    clients = []
    time_to_drive = 200


    # Start Clients
    for _ in range(0, num_clients):
        c = SimpleClient(address=(host, port))
        clients.append(c)

    time.sleep(1)

    # Load Scene message. Only one client needs to send the load scene.
    # msg = '{ "msg_type" : "load_scene", "scene_name" : "sparkfun_avc" }'
    msg = '{ "msg_type" : "load_scene", "scene_name" : "generated" }'
    clients[0].send_now(msg)


    # Send random driving controls
    start = time.time()
    do_drive = True
    clients[0].startTime = start
    while time.time() - start < time_to_drive and do_drive:
        for c in clients:
            c.update()
            if c.aborted:
                print("Client socket problem, stopping driving.")
                do_drive = False

    time.sleep(3.0)

    # Exit Scene - optionally..
    # msg = '{ "msg_type" : "exit_scene" }'
    # clients[0].send_now(msg)

    # Close down clients
    print("waiting for msg loop to stop")
    for c in clients:
        c.stop()

    print("clients to stopped")


if __name__ == "__main__":
    test_clients()
