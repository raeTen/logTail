#logTail 
is a small qick and dirty python log colourisation-tool which helps observing 
unix-style log files. It has several capabilities.

It will "tail" all files in a given directory (-d), or just a given
single file (-l). 
So you may have a "allmessages" or a path like "/var/log/logTail" with
any logfile you want to be tailed linked in.

It does simply the same as "tail -f", but also
for more logs at once and based on my first intention to have
colourised logs, it does exactly that on the fly.

logTail will read its configuration file at starting up,
and it will reload it automatically if it has been changed.

logTail also drops same lines in order, after REPLACEing keywords similar to any syslogd.
There's a "sensivity" (-s) for that. Default is 2. This means, logTail will say "repeated message"
when a maximum of 2 characters were different. Assigning -s 0 means, the lines have to be exactly 
the same to be dropped.

Here is a small description of what you can do within the configuration.
Ypp, again another configuration scheme, due to the fact, the
"ConfigParser" isn't (or was) case-sensitive.

Whitespaces within configuration are NOT ignored in the config, 
and everything is case-sensitive.

DROP{KEYWORD} FOObar 
Lines like " FOObar " would be - you guess it - dropped  while " foobar " won't

DROP{KEYWORD}Foo AND bar
Lines like "Something Foo somethingelse bar " are not shown (incl. whitespaces!)


REPLACE{ fooBaR }FooBAR
just replaces words (incl. whitespaces!) in a log line so
" fooBaR " results in "fooBAR"

REPLACE{DPT#}
This one will replace DPT=22 with nothing. The "#" means: Looking for DPT and the following up 
to the next whitespace even after REPLACE you might COLORize strings

Replacing doesn't work in dropped line of course.

COLOR{ FooBar:}bblack white blink
Colourises " FooBar:" in White on Black and let it blink 
(special esc sequences like blink will work on supported terminals only)

COLOR{DPT#}bred white
Colourises "DPT=FOO in white wit red background (next whitespace will reset the color to nomral...)
In detail the # separates the colouriser from the keyword to be searched.
In other words, "DPT" is the trigger to  colourise the string starting at "DPT" up to next whitespace,
so value pairs are treated dynamically.

Colourising will do its job pretty much after any "Replace"

logTail understands the following aliases of AnsiEsc Colours
Foreground:
black red green yellow blue magenta cyan white 
Background:
bblack bred bgreen byellow bblue bmagenta bcyan bwhite 
specials:
bold blink cright cleft cup cdown beep


POSTTRIGGER{firewallANDwarningANDfoobar}sudo /usr/sbin/beeper -f 2000 -l 100
This one does exactly what you expect. Please note that you may add an "&" to the commands...
Just let me know, if you need the "beeper.c" (which let you control the mainboard-beeper by frequency/length)
And at this point, hopefully the modern SoC will have a beeper in future again... :)

#Note
Everything works on-the-fly, your logs won't be touched at all.
Even though you are using -c(at) a single file #which DOES NOT work correctly yet!
Maybe I shoud fix that finally ;)

Another option is to "send" a "Replace-command" via the original log.
You may use something like "logger" on remote machines.

When logTail recognises (case-sensivite) "REPLACE key foo WITH bar value" in a line, it
will add/modify this on-the-fly. Tthose changes won't be written to configuration,
and so only available as long it loops.

For observing more than one logfile (-l /var/log/messages) you could use -d
for any directory. Ensure you have really plain-text logfiles within this given
directory only. /var/log/messages contains binary files  which
would messup the terminal screen of course.

# (my) best practice:

a) Create a "logtail" directory, e.g. /var/log/messages/logtail and symlink
any "wanted" logfile in there.
b) all your syslogds could use a single logserver. It has
many powerful mechanisms to do so. 
Depending on what,where and how much is being logged, you could start logTail
in different ways by renaming the .py file e.g. ./logTail2.py ./logTail_kern_log.py
and so on. Ensure to give any "logTail" a different configuration file by
passing it with -f (--configgile).

c) the start_logTail.sh starts a instance within a screen session, which is the most
useful way which I prefer.

d) have fun...
