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
# V 0.9.5  still some issues to fix with different terminals scrolling etc
# (c) 2008-2016 neTear 
#Thanks to every open mind for sharing all the good knowledge on computing
INTERNAL_PREFIX = "\033[1;31mlog\033[33mTail\033[37m:\033[0m "
FND_PREFIX="\033[30;1m" 
STATUS_PREFIX="\033[?25l"
VERSION = "0.9.5"
ETERNITY = True 
""" rescanning given destination-path after x seconds """
SCAN_INTERVAL = 20
"""second 0.5 - 5 are convenient TODO depending on logtraffic and cpu"""
POLLBASE = .9

KEYB = ( {'q':'quit', 'r':'replaced', 'd':'dropped',\
		  'h':'highlighted', 'p':'seen', 's':'stats',\
		  'c':'colourised', 't':'triggered','m':'repeated',\
		  'i':'statusline'}
		  )
import sys, os, time, getopt, string, fnmatch
from optparse import OptionParser
import datetime
import re

import threading, Queue
import tty, termios, atexit
LF="\r"
""" workaround getting one byte as keypress from stdin"""
old_settings = termios.tcgetattr(sys.stdin.fileno())
def clean_up_term():
	fd = sys.stdin.fileno()
	tty.setcbreak(sys.stdin.fileno())
	termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
	print "\033[?25h"+"\033[0m"+"Done"

def get_ch():
	fd = sys.stdin.fileno()
	old_settings = termios.tcgetattr(fd)
	try:
		tty.setraw(sys.stdin.fileno())
		ch = sys.stdin.read(1)
		sys.stdin.flush()
	finally:
		tty.setcbreak(sys.stdin.fileno())
		termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
	return ch

def add_input(input_queue):
	input_queue.put(get_ch())

def io_thread():
	input_queue = Queue.Queue()
	input_thread = threading.Thread(target=add_input, args=(input_queue,))
	input_thread.daemon = True
	input_thread.start()
	return input_queue

def file_init():
	atexit.register(clean_up_term)
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
	#parser.add_option("-o", "--output-file", dest = "catenateOutput", help = "-c cat(enate) -o foobar.txt writes to file instead to stdout", type = "string", default = "")
	parser.add_option("-s", "--sensivity", dest="sensivity",help = "Sensivity for dropping same log lines", type = "int", default = 2)
	parser.add_option("-m", "--message_repeated", dest = "mrp", help = "Tell about repeated messages", type="int", default = True)
	""" it does not make sense to convert microTimestamps since we'd need boot time from origin system"""
	parser.add_option("-k", "--kill-microTS", dest = "microTS", help = "replace microTS like [123123.123123] with something. -k \"\" will not replace", type = "string", default = "\033[41m \033[0m")
	parser.add_option("-p", "--print-filename", dest = "printFilename", help = "logTail inserts logfile names", type = "int", default = 1)
	parser.add_option("-l", "--limitFilename", dest = "limitFilename", help = "logTail truncates filenames to a maximum, recommends -p", type = "int", default = 0)
	parser.add_option("-i", "--infoline", dest = "infoLine", help = "displays a info status line", type = "int", default = 1)
	parser.add_option("-b", "--binary-check", dest = "binaryCheck", help = "-d 0 will switch off simple binary check on logfiles ", type = "int", default = 1)
	parser.add_option("-r", "--replace-logtime", dest = "replaceLogtime", help = "Tries to catch a logtime and truncates it", type = "int", default = 1)
	
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
	config["RE_TIME2"]= '.*?((?:(?:[0-1][0-9])|(?:[2][0-3])|(?:[0-9])):(?:[0-5][0-9])(?::[0-5][0-9])?(?:\\s?(?:am|AM|pm|PM))?)'
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

def pathScan(options, config, filenames, binary_filenames, pattern='*' ):
	try:
		names = os.listdir(options.logpath)
	except os.error:
		self_log(str(os.error))
		sys.exit(0)
	pattern = pattern or '*'
	pat_list = string.splitfields( pattern , ';' )
	maxlen = 8
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
									self_log(  "Found for tailing: "+fullname)
									filenames[fullname] = 0
								else:
									if not fullname in binary_filenames:
										binary_filenames.append(fullname)
									self_log(  "NOT tailing: "+fullname)
					except:
						self_log( str(sys.exc_info()[1]) )
				continue
	if not options.limitFilename:
		for f in filenames.keys():
			if len(os.path.basename(f)) > maxlen:
				maxlen = len(os.path.basename(f))
	else:
		maxlen = int(options.limitFilename) 
	config["limitFilename"] = maxlen
	return filenames, binary_filenames

def re_pathScan(options, config, filenames, binary_filenames):
	filenames, binary_filenames = pathScan(options, config, filenames, binary_filenames, '*')


def kill_microTS(checkline, microTS):
	m = re.findall(r"\[(\d*\.\d*)\]", checkline)
	if m:
		for match in m:
			checkline = checkline.replace("["+match+"]", microTS)
	return checkline

def replace_log_datetimes(rec, checkline):
	""" trying to minimize log-datetime stamps """
	try:
		trunc = checkline[:32]
		m = rec.search(trunc)
		if m:
			time_at = trunc.find(m.group(1))
		if time_at < 0:
			return checkline
		year_at = trunc.find('2016') #TODO
		if year_at > time_at:
				return FND_PREFIX + m.group(1) + '\033[0m' + checkline[year_at+4:]
		if time_at > 0:
			return FND_PREFIX + m.group(1) + '\033[0m' + checkline[time_at+len(m.group(1)):]
	except:
		pass
	return checkline

def compile_regexp(config):
	return re.compile(config["RE_TIME2"],re.IGNORECASE|re.DOTALL)

def act_time():
	return datetime.datetime.today().strftime("%H:%M:%S ")
	
def self_log(msg):
	print "\033[K"
	print "\033[2A"
	print INTERNAL_PREFIX + act_time() + msg + LF
	
def init_stats(stats):
	stats["dropped"] = 0
	stats["seen"] = 0
	stats["repeated"] = 0
	stats["replaced"] = 0
	stats["colourised"] = 0
	stats["highlighted"] = 0
	stats["triggered"] = 0
	
def print_status(config, key_flags, stats):
	if 'i' in key_flags.keys():
		print "\033[K\033[1A"
		return False
	tstat=""
	tinfo="      "
	for v in stats.keys():
		if v in key_flags.values():
			tstat = tstat+ STATUS_PREFIX + (v+":\033[1;5;31m"+"OFF"+"	\033[0m" + STATUS_PREFIX)
		else:
			tstat = tstat + STATUS_PREFIX + (v+":\033[1;32m"+str(stats[v])+"  \t\033[0m" + STATUS_PREFIX)
	if 'p' in key_flags.keys():
		tinfo=STATUS_PREFIX + "\033[1;5;33mPAUSED\033[0m" + STATUS_PREFIX
	#print "\033[s|u"
	print (
			STATUS_PREFIX +
			act_time() +
			STATUS_PREFIX+ tinfo +
			"	"+
			tstat +
			"\033[0m" +
			"\r" +
			config["MYCOLORS"].get("cup","1") 
		  ) 
	
def init_check(options):
	self_log("Version: "+VERSION+" remastered")
	if not options.logpath:
		self_log("No destination-path for logfiles given")
		sys.stdin = sys.__stdin__
		sys.exit(1)
	cf = options.configfile
	if not os.path.isdir(options.logpath):
		self_log("Missing -d(estination-path) or path does not exist")
		sys.exit(1)
	return options.configfile

def key_handler(key_flags, input_queue):
	key = input_queue.get()
	if key == 'q':
		sys.stdout = sys.__stdout__
		sys.stdin = sys.__stdin__
		sys.exit(0)
	
	if key in key_flags.keys():
		del key_flags[key]
	else:
		if len(key) == 1 and key in KEYB.keys():
			key_flags[key] = KEYB.get(key,0);
	#print key_flags
	input_queue = io_thread()
	return input_queue

def main():
	input_queue = io_thread()
	options = get_commandline_options()
	cf = init_check(options)
	catenate = options.catenate
	config = {}
	config, act_mdate = loadConfig(config, options)
	rec1 = compile_regexp(config)
	"""filename(s)+size(s)"""
	filenames = {}
	binary_filenames = []
	key_flags = {}
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
		filenames, binary_filenames = pathScan(options, config, filenames, binary_filenames, '*')
		if len(filenames) == 0:
			self_log(logpath+" is empty! Waiting for logfiles")
		self_log(  "-------------- starting -----------------")
		
		try:
			while ETERNITY: 
				""" main loop """
				print_status(config, key_flags, stats)
				if not input_queue.empty():
					input_queue = key_handler(key_flags, input_queue)
				time.sleep(POLLBASE)
				scan_cnt+=1
				if scan_cnt >= (float(1)/POLLBASE * SCAN_INTERVAL):
					re_pathScan(options, config, filenames, binary_filenames)
					scan_cnt=0
				act_mdate, reload_config = m_date(cf, act_mdate)
				if reload_config:
					self_log(  "Reloading configuration.")
					config, act_mdate = loadConfig(config, options)
				for filename in filenames.keys():
					try:
						file = open(filename,'r')
						""" file seeking """
						log_new_size = os.stat(filename)[6]
						log_act_size = filenames.get(filename, 0)
						if 'p' in key_flags.keys():
							log_new_size = log_act_size
						if log_act_size > log_new_size:
							self_log(  "Resetting seek position for "+filename)
							filenames[filename] = log_new_size
						if log_new_size > log_act_size:
							seek_pos = log_act_size
							if log_act_size == 0: #we just started
								seek_pos = log_new_size
							else:
								seek_pos = log_act_size
							file.seek(seek_pos)
							filenames[filename] = log_new_size
							lines = file.read().split('\n')
							for line in lines:
								if len(line) > 0:
									if not 'm' in key_flags.keys():
										sens = myDiffer(options.sensivity, line, bufferline)
										if sens >= options.sensivity:
											if scnt > 0:
												if options.mrp > 0:
													self_log(  "Last message repeated "+str(scnt)+" times")
												scnt = 0
										else:
											stats["repeated"] += 1
											scnt+=1
										bufferline = line
									if not scnt: 
										if options.microTS:
											line = kill_microTS(line, options.microTS)
										lastline = line_handler(key_flags, rec1, config, options, stats, catenate, line)
										add_filename = ""
										if len(lastline) > 0:
											if options.printFilename:
												pfilename=os.path.basename(filename).ljust(int(config["limitFilename"]))[0:(int(config["limitFilename"]))]
												add_filename = FND_PREFIX + pfilename + ' \033[0m'
											
											if options.replaceLogtime:
												try:
													lastline = replace_log_datetimes(rec1, lastline)
												except:
													print str(sys.exc_info()[1]) + LF
													pass
											"""highlight"""
											for hl in config["HIGHLIGHT"].keys():
												if lastline.find(hl) >- 1:
													stats["highlighted"] += 1
													hlv = config["HIGHLIGHT"].get(hl, 0)
													#hm underscore so set at begin and after all 0m?
													#self_log(  "to be highlighted with "+hlv+" linelength="+str(len(lastline)) )
											""" main out"""
											print "\033[K"
											print "\033[A"+add_filename + lastline + LF
											print_status(config, key_flags, stats)

											stats["seen"] += 1
											scnt=0
					except:
						print INTERNAL_PREFIX + str(sys.exc_info()[1]) + config["MYCOLORS"].get("cup","1")
						self_log(filename+" missing. Tailing stopped.")
						del filenames[filename]
						pass
		except:
			self_log(  "\nAborting. Should only happen by termination (q(uit) kill, ctrl-c ...).")
			latesterror=str(sys.exc_info()[1])
			if latesterror:
				self_log(  "Latest error: "+latesterror)
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
						lastline = line_handler(key_flags, config, options, stats, catenate, line)
						if options.catenateOutput:
							sys.stdout.write('.')
						else:
							if len(lastline) > 0:
								sens = myDiffer(options.sensivity, lastline, bufferline)
								if sens >= options.sensivity:
									if scnt > 0 and options.mrp > 0:
										self_log(  "Last message repeated "+str(scnt)+" times")
									print lastline
								
								scnt=0
							else:
								scnt+=1
							bufferline = lastline
			except:
				print str(sys.exc_info()[1])
				
		else:
			self_log(  "No regular file")

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
		

def log_handler(config, stats, l):
	""" add config values via log itself """
	hit = False
	if l.find('LOGTAILCLEAR')>-1:
		hit = True
		for v in config["REMOTEREPLACE"].keys():
			self_log(  "Removing from being replaced:"+v+" WITH "+str(config["REMOTEREPLACE"][v]))
			del config["REPLACE"][v]
			del config["REMOTEREPLACE"][v]

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
				self_log(  "Now replacing <"+key+"> with <"+val+">")
	return hit

def line_drop(rec1, config, options, stats, catenate, l):
	for dropw in config["DROP"].keys():
		if dropw.find('_AND_')>-1:
			acnt=0
			and_dropws = dropw.split('_AND_')
			for and_dropw in and_dropws:
				if l.find(and_dropw)>-1:
					acnt+=1
			if acnt == len(and_dropws):
				l=""
				stats["dropped"] += 1
		else:
			if l.find(dropw)>-1:
				l=""
				stats["dropped"] += 1
	return l

def line_replace(rec1, config, options, stats, catenate, l):
	for word in config["REPLACE"].keys():
		wf = False #word as field
		if word.find('#') > -1:
			wf = True
			word = word.replace('#',"")
		if l.find(word)>-1:
			if not wf:
				l=l.replace(word,config["REPLACE"].get(word,""))
				stats["replaced"] += 1
			else: #del from word to next whitespace
				ebuf=""
				buf=l.split()
				for elem in buf:
					if elem.find(word)>-1:
						elem = config["REPLACE"].get(word+'#',"")
					ebuf=ebuf+" "+elem
				l=ebuf
				stats["replaced"] += 1
	return l

def line_color(rec1, config, options, stats, catenate, l):
	for colkey in config["COLOR"].keys():
		origColKey = colkey
		wf = False
		if colkey.find('#')>-1:
			""" used to mark keyword as field, next whitespace demarks """
			colkey = colkey.replace('#','')
			wf = True
		i=l.find(colkey)
		if i>-1:
			ansi=config["COLOR"].get(origColKey,"")
			Tansi=ansi.split()
			Tcol=""
			for iansi in Tansi:
				Tcol = Tcol + config["MYCOLORS"].get(iansi,"")
			if not wf:
				l = l.replace(colkey,Tcol+colkey+chr(27)+"[0m")
				stats["colourised"] += 1
			else:
				ebuf=""
				append=""
				buf=l.split()
				for elem in buf:
					if elem.find(colkey)>-1:
						elem = elem.replace(colkey,Tcol+colkey)
						append = chr(27)+"[0m"
						stats["colourised"] += 1
					ebuf=ebuf+" "+elem+append
					append=""
				l=ebuf
	return l

def line_trigger(rec1, config, options, stats, catenate, l):
	for trigger in config["POSTTRIGGER"]:
		t=""
		if trigger.find('_AND_')>-1:
			acnt=0
			and_triggers = trigger.split('_AND_')
			for and_trigger in and_triggers:
				if l.find(and_trigger)>-1:
					acnt+=1
			if acnt == len(and_triggers):
				t = config["POSTTRIGGER"].get(trigger,"")
			else:
				if l.find(trigger)>-1:
					t = config["POSTTRIGGER"].get(trigger,"").strip()
		if len(t)>3:
			sp=""
			if t.find('_LINE_') >-1:
				t = t.replace('_LINE_','')
				sp=' \"'+l+'\"'
			if t.find('_OLINE_') >-1:
				t = t.replace('_OLINE_','')
				sp=' \"'+ol+'\"'
			try:
				os.system(t+sp)
				stats["triggered"] += 1
			except:
				print str(sys.exc_info()[1])

def line_handler(key_flags, rec1, config, options, stats, catenate, l):
	""" not "one" but l(ine) """
	if log_handler(config,stats, l):
		l=""
		return l
	ol = l
	if not 'd' in key_flags.keys():
		l = line_drop(rec1, config, options, stats, catenate, l)
	if len(l) > 0:
		if not 'r' in key_flags.keys():
			l = line_replace(rec1, config, options, stats, catenate, l)
		if not 'c' in key_flags.keys():
			l = line_color(rec1, config, options, stats, catenate, l)
		
		if not catenate:
			if not 't' in key_flags.keys():
				line_trigger(rec1, config, options, stats, catenate, l)
	return l

def create_conf(filename):
	defconf = ('#sample configuration for logTail,\n\
				DROP{FOO _AND_ Bar}\n\n\
				REPLACE{hostname_AND_Foo} Bar\n\n\
				COLOR{keyword after being replaced}blue beep\n\n\
				HIGHLIGHT{keyword after being replaced}\
				POSTTRIGGER{Firewall}beep &' )
	try:
		nconf=open(filename, "w")
	except:
		return False
	nconf.write(defconf)
	nconf.close()
	return True

if __name__ == '__main__':
	main()