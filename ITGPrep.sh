#!/bin/bash

killall ITGSend
killall ITGRecv
ITGRecv &
ITGSend -Q -L 192.168.109.213 &


