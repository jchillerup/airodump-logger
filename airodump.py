#!/usr/bin/python
#
# Copyright (C), Jens Christian Hillerup, BIT BLUEPRINT ApS (jc@bitblueprint.com)
#
# The following is a wrapper around airodump-ng to collect information about wireless APs/clients
# http://www.aircrack-ng.org/doku.php?id=airodump-ng
#

import os,sys,time, traceback, pexpect

DEBUG=True

class AirodumpProcessor:
    # Command to laucnh airodump-ng with:
    CMD="airodump-ng --update 1 --berlin 20 mon0"

    screen = None
    ap_list_on = 0
    client_list_on = 0
    ap_list = {}
    client_list = {}

    def __init__(self):
        pass

    def start(self):
        # Spawn the process in a Pexpect container.
        self.screen = pexpect.spawn(self.CMD)

        # Allocate a sufficiently large screen for the airodump-ng executable.
        self.screen.setwinsize(1000, 100)  # 1000 lines, 100 columns


    def process(self):
        if not self.screen:
            self.start()

        lines = []

        # Winch the window so we get enough clients.
        self.screen.setwinsize(300, 100)

        # Scrape one full screen.
        line = self.screen.readline()
        while not "CH" in line:
            line = self.screen.readline()

        while not "\x1b[J\x1b[1" in line:
            lines.append(line.replace("(not associated)", "(not_associated)").strip())
            line = self.screen.readline()

        # Parse the scraped screen:

        # In this section, we're keeping a variable called section, which is incremented
        # every time the program sees an empty line. The screen looks like this (numbered for
        # reference):
        #
        # 01.
        # 02. CH 11 ][ Elapsed: 9 mins ][ 2014-06-13 15:34  ][ 47/ 55/  68
        # 03.
        # 04. BSSID              PWR  Beacons    #Data, #/s  CH  MB   ENC  CIPHER AUTH ESSID
        # 05. 7C:03:D8:CD:71:6B  -47     1061        0    0   1  54e. WPA2 CCMP   PSK  HomeBox-7165
        # 06. 24:A4:3C:1E:18:A0  -57     1757     2510    2   6  54e. WPA2 CCMP   PSK  WhatASpace
        # 07. < ... >
        # 08.
        # 09. BSSID              STATION            PWR   Rate    Lost  Packets  Probes
        # 10.
        # 11. (not associated)   00:0F:13:39:1F:15  -35    0 - 1     14      297
        # 12. 24:A4:3C:1E:18:80  F0:F6:1C:5D:1B:DE  -127    0e- 0e    70      676  WhatASpace
        # 13. < ... >
        #
        # We skip the first four lines because they don't contain any data that we need. Every time
        # we encounter an empty line (that happens twice, lines 08 and 10) we increment the section
        # variable. In state 0 we are looking at APs and in state 2 we are looking at clients.
        # (TODO: there is probably a nicer itertools-based solution to this problem...)

        section = 0
        for line in lines[4:]:
            if line == "":
                section += 1
                continue
            # TODO: We're not scraping for APs (section == 0).
            if section == 2:
                v = line.split()

                CLIENT = v[1]
                if not self.client_list.has_key(CLIENT):
                    self.client_list[CLIENT] = {}

                self.client_list[CLIENT]["ap"]      = CLIENT
                self.client_list[CLIENT]["client"]  = v[1]
                self.client_list[CLIENT]["pwr"]     = v[2]
                self.client_list[CLIENT]["rate"]    = v[3]
                self.client_list[CLIENT]["lost"]    = v[4]
                self.client_list[CLIENT]["packets"] = v[5]

        return [self.ap_list, self.client_list]

    def stop(self):
        self.screen.terminate()
