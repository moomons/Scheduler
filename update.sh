#!/bin/bash

echo 'Version 0.10'
echo -e 'Script function: Backup and replace some Hadoop modules.\n Author: mons \n Date: 2016/04/10\n'

cd '~/hadoop/hadoop-2.7.1/share/hadoop/mapreduce/'

if [ ! -f 'hadoop-mapreduce-client-core-2.7.1.jar.ORIGINAL' ]; then
    echo "Backup file NOT FOUND. Renamed original file to .jar.ORIGINAL"
    mv 'hadoop-mapreduce-client-core-2.7.1.jar' 'hadoop-mapreduce-client-core-2.7.1.jar.ORIGINAL'
else
	echo "Backup file already there. Deleting the current jar ..."
	rm 'hadoop-mapreduce-client-core-2.7.1.jar'
fi

echo 'Downloading latest jar from mons:'
wget 'http://home.ustc.edu.cn/~mons/hadoop-mapreduce-client-core-2.7.1.jar'

echo 'Done.'

ls -la

