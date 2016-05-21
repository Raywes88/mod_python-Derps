'''
Any command that requires sudo has been added to /etc/sudoers to allow
the http user to run them without authenticating. This _should_ be alright...
You can't log in as the http user, and these commands are pretty harmless anyway.

Changes made to /etc/sudoers:
http ALL = NOPASSWD: /usr/sbin/hddtemp
http ALL=(usul) NOPASSWD: /usr/bin/transmission-daemon
http ALL = NOPASSWD: /home/usul/torrent_down.sh
http ALL = NOPASSWD: /home/usul/scrub_pool.sh

Using mod_python #yolo...
Each method below becomes a resource that can be requested from the server ie:
http://arrakis:50000/py_bin/index.py/info
^ when requested, the server executes the info method below and returns the output
to the requester.
'''
from mod_python import apache, util
from subprocess import Popen, PIPE

def info(req):
   argsdict = parseGET(req.args) #Parse url args into a dict

   #http boilerplate
   req.content_type = 'text/html'
   req.send_http_header()

   #Write the beginning of the page
   req.write("<html>")
   req.write("<title>Server Info</title>")
   req.write("<body vlink=\"blue\">") #Don't change color of visted links bruh
   req.write('<a href="http://arrakis:50000/py_bin/index.py/torrentup">Launch Transmission</a><br>')
   req.write('<a href="http://arrakis:50000/py_bin/index.py/torrentdown">Kill Transmission</a><br><br>')
   req.write('<a href="http://arrakis:50000/py_bin/index.py/scrubpool">Scrub RAID pool</a><br>')

   #Uptime 
   req.write("<h4>Uptime</h4>")
   req.write('<pre>')
   for line in command('iostat -c'):
      req.write(line)
   req.write('</pre>')
   for line in command('uptime'):
      req.write(line)
   
   #df - h
   req.write("<h4>Disk Usage</h4>")
   req.write("<pre>")
   bold = True
   for line in command('df -h'):
      if(bold):
         req.write("<b>")
      req.write(line)
      if(bold):
         req.write("</b>")
         bold = False
         
   req.write("\n")

   #iostat disk usage report since boot
   bold = True
   for line in commandL('iostat -d')[2:]:
      if(bold):
         req.write("<b>")
      req.write(line)
      if(bold):
         req.write("</b>")
         bold = False
   req.write("</pre>")

   #Hard drive temps; Requires root... wtf?
   req.write("<h4>HDD Temps</h4>")
   for line in command('sudo hddtemp /dev/sdb1'):
      req.write(line[:-4] + line[-3:]) #Check out this fuckin hack... kek
   req.write('<br>')
   for line in command('sudo hddtemp /dev/sdc1'):
      req.write(line[:-4] + line[-3:])

   req.write("<h4>RAID Status</h4>")
   req.write("<pre>")
   for line in command('cat /proc/mdstat'):
      req.write(line)
   req.write("</pre>")

   #Close the rest of the html tags and return
   req.write("</body>")
   req.write("</html><br><br><br>")
   return apache.OK

'''
Launches the transmission client as my user on the server.

@todo: Issue redirect to get back to info page instead of calling info() here.
'''
def torrentup(req):
   #needs to be run as 'usul' without pw some sudoers wizardry was required
   command('sudo -u usul /usr/bin/transmission-daemon')
   
   #If we've gotten this far, render the main page and exit
   return info(req)

'''
Kills the transmission process, if it is running.

@todo: Issue redirect to get back to info page instead of calling info() here.
'''
def torrentdown(req):
   #Created a shell script to avoid giving the http user the ability
   #to run killall without a pw. This just runs 'killall transmission-daemon'
   command('sudo ./home/usul/torrent_down.sh')

   #If we've gotten this far, render the main page and exit
   return info(req)

'''
Initiate RAID scrubbing

@todo: Issue redirect to get back to info page instead of calling info() here.
'''
def scrubpool(req):
   #This just runs 'echo check > /sys/block/md0/md/sync_action'
   command('sudo ./home/usul/scrub_pool.sh')

   #If we've gotten this far, render the main page and exit
   return info(req)

'''
Popen wrapper method for my own convenience.
Basically just cleans up the code above.

This is used to execute a command on the server and capture the output.
'''
def command(c):
   pipe = Popen(c, shell=True, stdout=PIPE)
   return pipe.stdout

'''
Version of command() that returns the output of the command as a list
of strings.
'''
def commandL(c):
   pipe = Popen(c, shell=True, stdout=PIPE)
   ret = []
   for line in pipe.stdout:
      ret.append(line)
   return ret

'''
Parses arguments supplied in the url ie:
?derp=poopballs&dale=jarrett

Returns a dict like so:
ret = {'derp': 'poopballs', 'dale': 'jarrett'}

All data is treated as strings. No attempt is made to parse
integers/floats at this point.
'''
def parseGET(args):
   ret = {}
   if not args:
      return ret
   derp = args.split('&')
   for d in derp:
      herp = d.split('=')
      ret[herp[0]] = herp[1]
   return ret
      
   
