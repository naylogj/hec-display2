#! /bin/sh
# /etc/init.d/owlmon

### BEGIN INIT INFO
# Provides:          rx-resol-payload-v3.py
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Simple script to start the rx-resol-payload-v3.py program
# Description:       Provides Solar Hot Water heating information for HEC display and Thingsboard
### END INIT INFO

# run every time commands here

# none

# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Starting resol"
    # run application you want to start
    /home/pi/resol/bin/startresol
    ;;
  stop)
    echo "Stopping resol"
    # kill application you want to stop
    sudo killall rx-resol-payload-v3.py
    ;;
  *)
    echo "Usage: /etc/init.d/resol {start|stop}"
    exit 1
    ;;
esac

exit 0
