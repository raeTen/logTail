#!/usr/bin/python
# -*- coding: utf-8 -*- 
# LogTail is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# My requirement for later versions: There is no possibility to transfer it into closed source.
# LogTail has been developed for reasons mentioned in the readme.txt,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# V 0.9.4 (remastered)
# (c) 2008-2016 neTear 
#Thanks to every open mind for sharing all the good knowledge on computing
#from __future__ import with_statement
INTERNAL_PREFIX = "\033[1;31mlog\033[33mTail\033[37m:\033[0m "
VERSION = "0.9.4"
ETERNITY = True 
""" rescanning given destination-path after x seconds """
SCAN_INTERVAL = 20
"""second 0.5 - 5 are convenient TODO depending on logtraffic and cpu"""
POLLBASE = .8
import os, time, sys, getopt, string, fnmatch
from optparse import OptionParser
import datetime
import re

def file_init():
	try:
		onearg=sys.argv[1]
	except:
		onearg=""
	conffile='logtail.conf'
	if not os.path.isfile(conffile):
		self_log(conffile+" not found in path")
		if not os.path.isfile('/etc/'+conffile):
			self_log(conffile+' not found in /etc... creating one locally')
			if not create_conf(conffile):
				self_log ("Error while creating a default config")
		else:
			conffile='/etc/'+conffile
	else:
		self_log("Configuration File:"+conffile)
	return onearg, conffile

def get_commandline_options():
	onearg, conffile = file_init()
	parser = OptionParser()
	parser.add_option("-f", "--configfile", dest = "configfile", help = "Location of configfile while not present within etc or bin-directory", type = "string", default = conffile)
	parser.add_option("-d", "--destination-path", dest = "logpath",help = "Tails all files in this destination path", type = "string", default = onearg)
	parser.add_option("-c", "--catenate", dest = "catenate", help = "-c cat(enate) and colourise given file completely on the fly", type = "string", default = "")
	parser.add_option("-o", "--output-file", dest = "catenateOutput", help = "-c cat(enate) -o foobar.txt writes to file instead to stdout", type = "string", default = "")
	parser.add_option("-s", "--sensivity", dest="sensivity",help = "Sensivity for dropping same log lines", type = "int", default = 2)
	parser.add_option("-m", "--message_repeated", dest = "mrp", help = "Tell about repeated messages", type="int", default = 1)
	""" it does not make sense to convert microTimestamps since we'd need boot time from origin system"""
	parser.add_option("-k", "--kill-microTS", dest = "microTS", help = "replace microTS like [123123.123123] with something. -k \"\" will not replace", type = "string", default = "\033[41m \033[0m")
	parser.add_option("-i", "--internal-info", dest = "internalInfo", help = "logTail gives internal informations", type = "int", default = 1)
	parser.add_option("-p", "--print-filename", dest = "printFilename", help = "logTail inserts logfile names ", type = "int", default = 1)
	parser.add_option("-b", "--binary-check", dest = "binaryCheck", help = "-d 0 will switch off simple binary check on logfiles ", type = "int", default = 1)
	(options, args)=parser.parse_args()
	return options
	  
def init_ansi_colors(config):
	ansi3 = ['black','red','green','yellow','blue','magenta','cyan','white']
	ansi4 = ['bblack','bred','bgreen','byellow','bblue','bmagenta','bcyan','bwhite']
	ansi5 = ['reverse#7m','underscore#4m','concealed#8m','bold#1m','blink#5m','cright#1C','cleft#1D','cup#1A','cdown#1B']
	esc = chr(27)+"["
	n=0
	mycolors={}
	for a in ansi3:
		mycolors[a] = esc+"3"+str(n)+"m"
		n+=1
	n=0
	for a in ansi4:
		mycolors[a] = esc+"4"+str(n)+"m"
		n+=1
	n=0
	for a in ansi5:
		ab=a.split('#');
		mycolors[ab[0]] = esc+ab[1]
	mycolors["beep"] = "\07"
	mycolors["wuff"] = esc+"1;31mWuff \033[33mWuff \033[36mWuff \033[37m...\033[0;1;32m"
	config["MYCOLORS"] = mycolors

def m_date(conf_filename, act_mdate):
	ts = os.path.getmtime(conf_filename)
	return ts, (ts != act_mdate)


def show_config(chain):
	tmpvals=""
	for value in conf_dict.keys():
		tmpvals=tmpvals+conf_dict.get(value,0)+" "+value+"|"
	self_log(confcategory+":"+tmpvals)
	

def loadConfig(config, options):
	file = options.configfile
	ln = 0
	chainbuf = {}
	chains = ["POSTTRIGGER","COLOR","DROP","REPLACE","HIGHLIGHT","REMOTEREPLACE"]
	if len(config.keys()): # == 0:
		chainbuf = config["REMOTEREPLACE"]
	config = {}
	for chain in chains:
			config[chain] = {}
	cfile = open(file, "r")
	lines = cfile.read().split('\n')
	act_mdate, reload_config = m_date(file, 0)
	cfile.close()
	for line in lines:
		ln += 1
		if line:
			if line[0]!="#":
				try:
					chain=line.split('{')[0]
					key=line.split('{')[1].split('}')[0]
					val=line.split('}')[1]
					if len(key)>0:
						config[chain][key] = val
				except:
					self_log("Config Error at line "+str(ln)+"<"+line+">")
	if len(chainbuf.keys())>0:
		config["REMOTEREPLACE"] = chainbuf
		for v in chainbuf.keys():
			config["REPLACE"][v] = chainbuf[v]
	init_ansi_colors(config)
	return config, act_mdate

def isText(filename, binaryCheck):
	""" simple protection, logTail will mess up terminal by processing binary logfiles """
	if binaryCheck:
		f = open(filename, 'rb')
		try:
			while ETERNITY:
				chunk = f.read(512)
				if '\0' in chunk: 
					return False
				if len(chunk) < 512:
					break
		finally:
		  f.close()
	return True

def pathScan(options, filenames, binary_filenames, pattern='*' ):
	try:
		names = os.listdir(options.logpath)
	except os.error:
		self_log(str(os.error))
		return filenames
	pattern = pattern or '*'
	pat_list = string.splitfields( pattern , ';' )
	for name in names:
		fullname = os.path.normpath(os.path.join(options.logpath, name))
		# grab if it matches our pattern and entry type
		for pat in pat_list:
			if fnmatch.fnmatch(name, pat):
				if os.path.isfile(fullname):
					try:
						if not fullname in binary_filenames:
							if not fullname in filenames.keys():
								if isText(fullname, options.binaryCheck):
									self_log("Found for tailing: "+fullname)
									filenames[fullname] = 0
								else:
									if not fullname in binary_filenames:
										binary_filenames.append(fullname)
									self_log("NOT tailing: "+fullname)
					except:
						self_log(str(sys.exc_info()[1]) )
				continue
	return filenames, binary_filenames

def re_pathScan(options, filenames, binary_filenames):
	filenames, binary_filenames = pathScan(options, filenames, binary_filenames, '*')


def kill_microTS(checkline, microTS):
	m = re.findall(r"\[(\d*\.\d*)\]", checkline)
	if m:
		for match in m:
			checkline = checkline.replace("["+match+"]", microTS)
	return checkline

def self_log(msg):
	tformat = "%b %d %H:%M:%S "
	today = datetime.datetime.today()
	s = today.strftime(tformat)
	print s + INTERNAL_PREFIX + msg

def init_stats(stats):
	stats["dropped"] = 0
	stats["seen"] = 0
	stats["repeated"] = 0

def main():
	self_log("Version: "+VERSION+" remastered")
	options = get_commandline_options()
	if not options.logpath:
		self_log("No destination-path for logfiles given")
		sys.exit(1)
	cf = options.configfile
	catenate = options.catenate
	config = {}
	config, act_mdate = loadConfig(config, options)

	"""filename(s)+size(s)"""
	filenames = {}
	binary_filenames = []
	stats = {}
	init_stats(stats)
	lastline = ""
	bufferline = ""
	scnt = 0
	seek_pos = 0
	scan_cnt = 0
	for trigger in config["POSTTRIGGER"].keys():
		self_log("WARN: '"+trigger+"' executes -> "+ config["POSTTRIGGER"].get(trigger,""))
		
	if not catenate:
		filenames, binary_filenames = pathScan(options, filenames, binary_filenames, '*')
		if len(filenames) == 0:
			self_log(logpath+" is empty! Waiting for logfiles")
		self_log("-------------- starting -----------------")
		
		try:
			while ETERNITY: 
				""" main loop """
				time.sleep(POLLBASE)
				scan_cnt+=1
				if scan_cnt >= (float(1)/POLLBASE * SCAN_INTERVAL):
					""" handle research on logfiles in given path """
					re_pathScan(options, filenames, binary_filenames)
					scan_cnt=0
				act_mdate, reload_config = m_date(cf, act_mdate)
				if reload_config:
					self_log("Reloading configuration.")
					config, act_mdate = loadConfig(config, options)
				for filename in filenames.keys():
					try:
						file = open(filename,'r')
						""" Find the size of the file and move to the end """
						log_new_size = os.stat(filename)[6]
						log_act_size = filenames.get(filename, 0)
						if log_act_size > log_new_size:
							self_log("Resetting seek position for "+filename)
							filenames[filename] = log_new_size
						if log_new_size > log_act_size:
							seek_pos = log_act_size
							if log_act_size == 0: #we just started
								if log_new_size > 1024:
									seek_pos = log_new_size - 1024
							else:
								seek_pos = log_act_size
							file.seek(seek_pos)
							filenames[filename] = log_new_size
							lines = file.read().split('\n')
							for line in lines:
								if len(line)>0:
									if options.microTS:
										line = kill_microTS(line, options.microTS)
									lastline=line_handler(config, stats, catenate, line)
									if len(lastline) > 0:
										sens = myDiffer(options.sensivity, lastline, bufferline)
										if sens >= options.sensivity:
											if scnt > 0 and options.mrp > 0:
												self_log("Last message repeated "+str(scnt)+" times")
												stats["repeated"] += scnt
											print lastline
											stats["seen"] += 1
											scnt=0
										else:
											scnt+=1
										bufferline = lastline
					except:
						print INTERNAL_PREFIX + str(sys.exc_info()[1]) + config["MYCOLORS"].get("cup","1")
						self_log(filename+" missing. Tailing stopped.")
						del filenames[filename]
						pass
		except:
			self_log("\nAborting. Should only happen by external termination (kill, ctrl-c ...).")
			latesterror=str(sys.exc_info()[1])
			if latesterror:
				self_log("Latest error: "+latesterror)
	else: 
		""" just proceed a catenate """
		if os.path.isfile(catenate):
			try:
				file=open(catenate, 'r')
				lines=file.read().split('\n')
				for line in lines:
					if len(line)>0:
						if options.microTS:
							line = kill_microTS(line, options.microTS)
						lastline = line_handler(config, stats, catenate, line)
						if options.catenateOutput:
							sys.stdout.write('.')
						else:
							if len(lastline) > 0:
								sens = myDiffer(options.sensivity, lastline, bufferline)
								if sens >= options.sensivity:
									if scnt > 0 and options.mrp > 0:
										self_log("Last message repeated "+str(scnt)+" times")
									print lastline
								
								scnt=0
							else:
								scnt+=1
							bufferline = lastline
			except:
				print str(sys.exc_info()[1])
				
		else:
			self_log("No regular file")

def myDiffer(sensivity, lastline, bufferline):
	""" differ won't work since it is not case-sens"""
	if lastline==bufferline:
		return 0
	elif len(lastline)==len(bufferline):
		diff=0
		for ch1,ch2 in zip(lastline, bufferline):
			if ch1 != ch1:
				diff+=1
				if diff>sensivity:
					return diff
		return diff
	elif len(lastline)!=len(bufferline):
		return abs(len(lastline)-len(bufferline))
		

def output_and_sensivity(diff, lastline, bufferline, sensivity, scnt):
	if len(lastline) > 0:
		linediff = string.join(diff.compare(lastline,bufferline))
		sens = len(linediff.split('+'))
		if sens > sensivity:
			if scnt > 0 and options.mrp > 0:
				self_log("Last message repeated "+str(scnt)+" times")
			print lastline
			scnt=0
		else:
			scnt+=1
		bufferline = lastline
	return scnt

def log_handler(config, stats, l):
	""" add config values via log itself """
	hit = False
	if l.find('LOGTAILCLEAR')>-1:
		hit = True
		for v in config["REMOTEREPLACE"].keys():
			self_log("Removing from being replaced:"+v+" WITH "+str(config["REMOTEREPLACE"][v]))
			del config["REPLACE"][v]
			del config["REMOTEREPLACE"][v]
	
	if l.find('LOGTAILSTATS')>-1:
		hit = True
		for v in stats.keys():
			self_log(v+" "+str(stats[v]))

	if l.find('LOGTAILREPLACE')>-1:
		lh=l.split('LOGTAILREPLACE')
		if len(lh)>=1:
			lf=lh[1]
			lh=lf.split('WITH')
			if lf.find('WITH') and len(lh)>=2:
				key=lh[0][1:][:-1]
				val=lh[1][1:]#[:-1]
				config["REPLACE"][key] = val
				config["REMOTEREPLACE"][key] = val
				hit = True
				self_log("Now replacing <"+key+"> with <"+val+">")
	return hit

def line_handler(config, stats, catenate, l):
	""" not "one" but l(ine) - all dropping and replacements and posttrigger here """
	if log_handler(config,stats, l):
		l=""
	for dropw in config["DROP"].keys():
		if dropw.find('_AND_')>-1:
			acnt=0
			and_dropws=dropw.split('_AND_')
			for and_dropw in and_dropws:
				if l.find(and_dropw)>-1:
					acnt+=1
			if acnt==len(and_dropws):
				l=""
				stats["dropped"] += 1
		else:
			if l.find(dropw)>-1:
				l=""
				stats["dropped"] += 1
	if len(l)>0:
		for word in config["REPLACE"].keys():
			word_asfield = False
			if word.find('#') > -1:
				word_asfield = True
				word=word.replace('#',"")
			if l.find(word)>-1:
				if not word_asfield:
					l=l.replace(word,config["REPLACE"].get(word,""))
				else: #del from word to next whitespace
					ebuf=""
					buf=l.split()
					for elem in buf:
						if elem.find(word)>-1:
							elem=config["REPLACE"].get(word+'#',"")
						ebuf=ebuf+" "+elem
					l=ebuf
		for colkey in config["COLOR"].keys():
			origColKey = colkey
			colkey_asfield = False
			if colkey.find('#')>-1:
				""" used to mark keyword as field, next whitespace demarks """
				colkey=colkey.replace('#','')
				colkey_asfield=True
			i=l.find(colkey)
			if i>-1:
				ansi=config["COLOR"].get(origColKey,"")
				Tansi=ansi.split()
				Tcol=""
				for iansi in Tansi:
					Tcol = Tcol + config["MYCOLORS"].get(iansi,"")
				if not colkey_asfield:
					l=l.replace(colkey,Tcol+colkey+chr(27)+"[0m")
				else:
					ebuf=""
					append=""
					buf=l.split()
					for elem in buf:
						if elem.find(colkey)>-1:
							elem=elem.replace(colkey,Tcol+colkey)
							append=chr(27)+"[0m"
						ebuf=ebuf+" "+elem+append
						append=""
					l=ebuf
		if not catenate:
			for trigger in config["POSTTRIGGER"]:
				t=""
				if trigger.find('_AND_')>-1:
					acnt=0
					and_triggers = trigger.split('_AND_')
					for and_trigger in and_triggers:
						if l.find(and_trigger)>-1:
							acnt+=1
					if acnt==len(and_triggers):
						t = config["POSTTRIGGER"].get(trigger,"")
				else:
					if l.find(trigger)>-1:
						t = config["POSTTRIGGER"].get(trigger,"").strip()
				if len(t)>3:
					try:
						os.system(t)
					except:
						print str(sys.exc_info()[1])
			l=l.strip()
	return l

def create_conf(filename):
	defconf='#sample configuration for logTail, see readme for more details\nDROP{FOO _AND_ Bar}\n\nREPLACE{hostname_AND_Foo} Bar\n\nCOLOR{Foo}blue bred bold blink beep\n\nPOSTTRIGGER{Firewall}beep &'
	try:
		nconf=open(filename, "w")
	except:
		return False
	nconf.write(defconf)
	nconf.close()
	return True

if __name__ == '__main__':
	main()