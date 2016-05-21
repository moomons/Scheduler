!/bin/bash

while true; do
killall ITGSend
killall ITGRecv
ITGRecv &
ITGSend -Q -L 192.168.109.213
done

