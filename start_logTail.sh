#!/bin/bash
#########################################################################################
#LogTail is free software; you can redistribute it and/or modify                         #
#it under the terms of the GNU General Public License as published by                    #
#the Free Software Foundation; either version 2 of the License, or                       #
#(at your option) any later version.                                                     #
#My requirement for later versions: There is no possibility to transfer it               #
#to closed source.                                                                       #
#LogTail has been developed for reasons mentioned in the readme.txt,                     #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                          #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                           #
#GNU General Public License for more details.                                            #
#You should have received a copy of the GNU General Public License                       #
#along with this; if not, write to the Free Software                                     #
#Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA              #
#                                                                                        #
#(c) 2008-2016 neTear                                                                         #
############################### CONFIG ###################################################
#logposition has to be a simple directory, just start logTail and create symlinks for 
#destination-path for logfiles to be processed by logTail
logposition=/var/log/logtail/
#if no given configuration file here, logTail tries to read /etc/logtail.conf#############
conffile=logtail.conf # the one in THIS directory 
#                                                                                        
logTail_bin=logTail.py  #the on in THIS directory may be logTail2.py for another instance
sensivity=3 #if empty logTail will use 2 as default                                      #
##########################################################################################
##########################################################################################
##########################################################################################
screen_bin=`which screen`
inhere=`pwd`
python_interpreter=`which python`
[ -z "$python" ] && echo "Python interpreter missing on system"
if [ -f "$logposition" ];then
    echo "logpostion has to be a path!"
    exit 0
fi
[ -d "$logposition" ] && logtail_p="-d $logposition"
[ -e "$inhere/$conffile" ] && logtail_p="$logtail_p -f $inhere/$conffile"
[ ! -z "$sensivity" ] && logtail_p="$logtail_p -s $sensivity"
if [ -z "$screen_bin" ]; then
    [ -e "$inhere/$logTail_bin" ] && $python_interpreter $inhere/$logTail_bin $logtail_p
else
    #using screen
    session=`echo $logTail_bin|awk -F "." '{ print $1 }'`
    session_exists=`$screen_bin -ls $session.session | grep $session`
    [ -z "$session_exists" ] && screen -mdS "$session.session"  $python_interpreter $inhere/$logTail_bin $logtail_p || echo "session exists"
    read -t 20 -n 1 -p "$logTail_bin has been started in screen $session.session, any key to continue, leaving screen session by CTRL+a and d (man screen)" answer
    #if you do sh instead of bash this "read" will fix issues...
    #read -p "$logTail_bin started in screen /"$sessnion/" session, any key to continue, leaving screen session by CTRL+a and d (man screen)" answer
    screen -x $session.session
fi
