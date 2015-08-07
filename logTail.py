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
# V 0.9.0
# (c) 2008 by neTear

import os, time, sys, getopt, string, fnmatch
from optparse import OptionParser
#from difflib import Differ <- not usable 

def file_init():
	try:
		onearg=sys.argv[1]
	except:
		onearg=""
	conffile='logtail.conf'
	if not os.path.isfile(conffile):
		print conffile+' not found in directory'
		if not os.path.isfile('/etc/'+conffile):
			print conffile+' not found in /etc... create one'
			if not create_conf(conffile):
				print 'Error while creating default config'
		else:
			conffile='/etc/'+conffile
	else:
		print 'Config:'+conffile
	return onearg, conffile

def get_commandline_options():
	onearg,conffile=file_init()
	parser = OptionParser()
	parser.add_option("-f","--configfile",dest="configfile",help="Location of configfile if not in /etc or bin-directory",type="string",default=conffile)
	parser.add_option("-d","--directory",dest="logdirectory",help="Tails all files in given directory",type="string",default=onearg)
	parser.add_option("-l","--logfile",dest="logfile",help="Tails given file",type="string",default="")
	parser.add_option("-c","--cat",dest="cat",help="-c implies -l and does exactly that, what you expect",type="string",default="")
	parser.add_option("-s","--sensivity",dest="sensivity",help="Sensivity for dropping same log lines",type="int",default=2)
	parser.add_option("-m","--message_repeated",dest="message_repeated",help="Tell about repeated messages",type="int",default=1)
	
	return parser


def init_ansi_colors():
	mycolors={}
	mycolors["black"] = chr(27)+"[30m"
	mycolors["red"] = chr(27)+"[31m"
	mycolors["green"] = chr(27)+"[32m"
	mycolors["yellow"] = chr(27)+"[33m"
	mycolors["blue"] = chr(27)+"[34m"
	mycolors["magenta"] = chr(27)+"[35m"
	mycolors["cyan"] = chr(27)+"[36m"
	mycolors["white"] = chr(27)+"[37m"
	
	mycolors["bblack"] = chr(27)+"[40m"
	mycolors["bred"] = chr(27)+"[41m"
	mycolors["bgreen"] = chr(27)+"[42m"
	mycolors["byellow"] = chr(27)+"[43m"
	mycolors["bblue"] = chr(27)+"[44m"
	mycolors["bmagenta"] = chr(27)+"[45m"
	mycolors["bcyan"] = chr(27)+"[46m"
	mycolors["bwhite"] = chr(27)+"[47m"
	
	mycolors["bold"] = chr(27)+"[1m"
	mycolors["blink"] = chr(27)+"[5m"
	mycolors["cright"] = chr(27)+"[1C"	#move <NUM> columns forward but only upto last column
	mycolors["cleft"] = chr(27)+"[1D"	#move <NUM> columns backward but only upto first column
	mycolors["cup"] = chr(27)+"[1A"	   	#move <NUM> rows up
	mycolors["cdown"] = chr(27)+"[1B"	#move <NUM> rows down
	mycolors["beep"] = chr(27)+"[7"
	mycolors["wuff"] = chr(27)+"[1;31mWuff \033[33mWuff \033[36mWuff \033[37m...\033[0;1;32m"
	return mycolors

def LoadConfig(file):
	cfile=open(file, "r")
	lines=cfile.read().split('\n')
	actsize = os.stat(file)[6]
	cfile.close()
	col_keyw = {}
	drop_lines_with = []
	replace_words = {}
	posttrigger_words = {}
	for line in lines:
		if line:
			if line[0]!="#":
				try:
					cat=line.split('{')[0]
					key=line.split('{')[1].split('}')[0]
					val=line.split('}')[1]
					if len(key)>0:
						if cat=="COLOR":
							col_keyw[key] = val
						elif cat=="DROP":
							drop_lines_with.append(val)
						elif cat=="REPLACE":
							replace_words[key]=val
						elif cat=="POSTTRIGGER":
							posttrigger_words[key]=val
				except:
					print "Config Error "+line
	return drop_lines_with, col_keyw, replace_words, posttrigger_words, actsize


def confSize(file, oldsize):
	actsize = os.stat(file)[6]
	if oldsize!= actsize:
		return actsize,True
	else:
		return actsize,False


def dirScan( root, pattern='*', return_folders=0 ):
	result = []
	# must have at least root dir
	try:
		names = os.listdir(root)
	except os.error:
		return result
	# expand pattern
	pattern = pattern or '*'
	pat_list = string.splitfields( pattern , ';' )
	# check each file
	for name in names:
		fullname = os.path.normpath(os.path.join(root, name))
		# grab if it matches our pattern and entry type
		for pat in pat_list:
			if fnmatch.fnmatch(name, pat):
				if os.path.isfile(fullname):# or (return_folders and os.path.isdir(fullname)):
					try:
						test=open(fullname, 'r')
						result.append(fullname)
					except:
						print str(sys.exc_info()[1])
				continue
	return result

def check_options(parser):
	(options,args)=parser.parse_args()
	dirname=options.logdirectory
	filename=options.logfile
	configfile=options.configfile
	message_repeated=options.message_repeated
	catfile=options.cat
	sensivity=options.sensivity
	if not type (sensivity) == int:
		sensivity=2
	print "Sensivity="+str(sensivity)
	if os.path.isfile(dirname):
			dirname=""
	else:
		if os.path.exists(dirname):
			pass
	if options.cat:
		catfile=options.cat
		return dirname,filename,configfile,catfile,sensivity,message_repeated
	if os.path.isfile(filename):
		dirname=""
	if dirname=="" and filename=="":
		parser.error("You need -d /path/logs/ or -l /path/logfile")
	if configfile!="":
		if not os.path.isfile(configfile):
			parser.error("Given configfile does not exist.")
	return dirname,filename,configfile,catfile,sensivity,message_repeated

def main():
	dirname,filename,configfile,catfile,sensivity,message_repeated=check_options(get_commandline_options())
	dlines, col_keyw, replace_words,posttrigger_words, actsize=LoadConfig(configfile)
	mycolors=(init_ansi_colors())
	filenames={}#filename(s)+size
	lastline=""
	bufferline=""
	scnt=0
	###############
	print posttrigger_words
	###############
	if not catfile:
		if filename=="":
			files = dirScan(dirname, '*', 1)
			if len(files) == 0:
				print 'Empty directory!'
				sys.exit(1)
			for filename in files:
				print 'Tailing file:', filename
				filenames[filename]=0
		else:
			try:
				chk=open(filename, 'r')
				filenames[filename]=0
			except:
				print str(sys.exc_info()[1])
				sys.exit(1)
		try:
			while True:
				time.sleep(1)
				actsize,reload=confSize(configfile, actsize)
				if reload:
					print "Reloading Config"
					dlines, col_keyw, replace_words, posttrigger_words, actsize=LoadConfig(configfile)
				for filename in filenames.keys():
					try:
						file = open(filename,'r')
						#Find the size of the file and move to  the end
						new_results = os.stat(filename)
						new_size = new_results[6]
						act_size=filenames.get(filename,0)
						if new_size > act_size:
							if act_size==0: #just started
								file.seek(new_size -924)
							else:
								file.seek(act_size)
							filenames[filename]=new_size
							lines = file.read().split('\n')
							for line in lines:
								if len(line)>0:
									lastline=line_handler(dlines, col_keyw, replace_words, posttrigger_words, mycolors, line)
									if len(lastline)>0:
										sens=myDiffer(sensivity, lastline, bufferline)
										if sens>=sensivity:
											if scnt>0 and message_repeated >0:
												print "Last message repeated "+str(scnt)+" times"
											print lastline
											scnt=0
										else:
											scnt+=1
										bufferline=lastline
					except:
						print str(sys.exc_info()[1])+mycolors.get("cup","1")
						pass
		except:
			print "Aborting"
	else: #cat a file
		if os.path.isfile(catfile):
			try:
				file=open(catfile, 'r')
				lines=file.read().split('\n')
				for line in lines:
					lastline=line_handler(dlines, col_keyw, replace_words, posttrigger_words, mycolors, line)
					scnt=output_and_sensivity(diff, lastline, bufferline, sensivity, scnt)
			except:
				print str(sys.exc_info()[1])
				
		else:
			print "No regular file"

def myDiffer(sensivity, lastline, bufferline):
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
	#diff=Differ()
	if len(lastline)>0:
		linediff=string.join(diff.compare(lastline,bufferline))
		sens=len(linediff.split('+'))
		if sens>sensivity:
			if scnt>0 and message_repeated >0:
				print "Last message repeated "+str(scnt)+" times"
			print lastline
			scnt=0
		else:
			scnt+=1
		bufferline=lastline
	return scnt

def log_handler(dlines, col_keyw, replace_words, posttrigger_words, mycolors, l):
	if l.find('REPLACE')>-1:
		lh=l.split('REPLACE')
		if len(lh)>=1:
			lf=lh[1]
			lh=lf.split('WITH')
			if lf.find('WITH') and len(lh)>=2:
				key=lh[0][1:][:-1]
				val=lh[1][1:][:-1]
				replace_words[key]=val
				print "Now replacing <"+key+"> with <"+val+">"
				print replace_words
				
def line_handler(dlines, col_keyw, replace_words, posttrigger_words, mycolors, l):
	log_handler(dlines, col_keyw, replace_words, posttrigger_words, mycolors, l)
	for dropw in dlines:
		if dropw.find('AND')>-1:
			acnt=0
			and_dropws=dropw.split('AND')
			for and_dropw in and_dropws:
				if l.find(and_dropw)>-1:
					acnt+=1
			if acnt==len(and_dropws):
				l=""
		else:
			if l.find(dropw)>-1:
				l=""
	if len(l)>0:
		for word in replace_words.keys():
			word_asfield=False
			if word.find('#')>-1:
				word_asfield=True
				word=word.replace('#',"")
			if l.find(word)>-1:
				if not word_asfield:
					l=l.replace(word,replace_words.get(word,""))
				else: #del from word to next whitespace
					ebuf=""
					buf=l.split()
					for elem in buf:
						if elem.find(word)>-1:
							elem=replace_words.get(word+'#',"")
						ebuf=ebuf+" "+elem
					l=ebuf
				#print "replaced "+word+" "+replace_words.get(word,"1")
		for colkey in col_keyw.keys():
			origColKey=colkey
			colkey_asfield=False
			if colkey.find('#')>-1:  #used to mark keyword as field, next whitespace separates
				colkey=colkey.replace('#','')
				colkey_asfield=True
			i=l.find(colkey)
			if i>-1:
				ansi=col_keyw.get(origColKey,"")
				Tansi=ansi.split()
				Tcol=""
				for iansi in Tansi:
					Tcol=Tcol+mycolors.get(iansi,"")
				if not colkey_asfield:
					l=l.replace(colkey,Tcol+colkey+chr(27)+"[0m")
				else:
					#print "Using as field <"+colkey+">"+Tcol
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
		for trigger in posttrigger_words:
			t=""
			if trigger.find('AND')>-1:
				acnt=0
				and_triggers=trigger.split('AND')
				for and_trigger in and_triggers:
					if l.find(and_trigger)>-1:
						acnt+=1
				if acnt==len(and_triggers):
					t=posttrigger_words.get(trigger,"")
			else:
				if l.find(trigger)>-1:
					t=posttrigger_words.get(trigger,"").strip()
			if len(t)>3:
				try:
					os.system(t)
				except:
					print str(sys.exc_info()[1])
		l=l.strip()
	return l

def create_conf(filename):
	defconf='#sample configuration for logTail, see readme for more details\nDROP{KEYWORD}Foo Bar\n\nREPLACE{hostnameANDFoo} Bar\n\nCOLOR{Foo}blue bred bold blink beep\n\nPOSTTRIGGER{Firewall}beep &'
	try:
		nconf=open(filename, "w")
	except:
		return False
	nconf.write(defconf)
	nconf.close()
	return True

if __name__ == '__main__':
	main()