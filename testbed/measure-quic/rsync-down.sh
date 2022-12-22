#!/bin/bash
echo "Synchronizing files .."

source ~/.bash_profile
#sync only a specific folder
#FOLDER="anastacia"
FOLDER="."


TARGET=measure-quic
USER=montimage
IP=192.168.1.106
PORT=10081

# -W : disables delta/diff comparisons. When the file time/sizes differ, rsync copies the whole file.
#rsync -e "ssh -i /Users/nhnghia/.ssh/id_rsa $(ssh-jump-path-mi montimage@192.168.0.235) -p $PORT" -rcav --progress "$USER@$IP:$TARGET/log-*" ./
#rsync -e "ssh -i /Users/nhnghia/.ssh/id_rsa -J montimage@192.168.0.42 -p $PORT" -rcav --progress "$USER@$IP:$TARGET/log-*" ./
rsync -e "ssh -i /Users/nhnghia/.ssh/id_rsa -J montimage@192.168.0.235:$PORT" -rcav --progress "$USER@$IP:$TARGET/*" ./


#RUN="cd build && make -j4"
#RUN="cd build && cmake .."

#echo "Compiling `pwd` ... on $USER@$IP:$TARGET"
#echo "Run: $RUN"

#ssh -p $PORT $USER@$IP "cd $TARGET && $RUN"
