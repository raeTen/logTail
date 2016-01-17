#logTail 
##remastered 
is a small qick and dirty python log colourisation-tool which helps observing 
unix-style log files. It has several capabilities.
VERSION 0.9.4 has been completely remastered

It will "tail -f" all files in a given directory (-d[estination-path]), or just catenate a given
single file on-the-fly with -c(atenate). The latter won't trigger any "posttrigger",
but replacing and colourising like in "tailing-mode".

A cat(enate) could be piped to more|less, whereby "less" does support colors within
old DOS only. "more" works pretty good, so maybe I'll add a inbuilt-less
functionallity one day. |less -R(aw) might work.

You should have a dedicated path  like "/var/log/logTail" with
any logfile you want to be tailed by logTail
Just create or delete symlinks in there, logTail will recognise
them automatically.
logTail proceeds now any (non-binary) file on its own without restarting.
No further issues with e.g. logrotate truncated file.

It also reloads its configuration file after modification.
This way, your personal configuration will grow peu a peu ;-)

logTail also drops same lines in order, after REPLACEing the replacesment-keywords similar to any syslogd.
There's a "sensivity" (-s) for that. Default is 2. This means, logTail will say "repeated message"
when a maximum of 2 characters were different. Assigning -s 0 means, the lines have to be exactly 
the same to be dropped.

Here is a small description of what you can do within the configuration.
Yet, again another configuration scheme, due to the fact, the
"ConfigParser" isn't (or was) case-sensitive.

Whitespaces within configuration are NOT ignored and additionally 
everything is case-sensitive - unices-style.

>DROP{ FOObar}
Lines with " FOObar " would be - you guess it - dropped  while " foobar " won't

"_AND_" does a logical and on the given keywords
>DROP{KEYWORD}Foo_AND_ bar
Lines like "Something Foo somethingelse bar " are dropped (watch the whitespaces!)


>REPLACE{ fooBaR }FooBAR
just replaces words (incl. whitespaces!) in a log line so
" fooBaR " results in "fooBAR"
while
>REPLACE{ fooBaR } FooBAR 

" fooBaR " results in " fooBAR "


>REPLACE{DPT#}
This one will replace DPT=22 with nothing. The "#" means: Looking for DPT and the following up 
to the next whitespace even after REPLACE you might COLORise strings

Replacing doesn't work in dropped line of course.

>COLOR{ FooBar:}bblack white blink
Colourises " FooBar:" in White on Black and let it blink
(special esc sequences like blink will work on supported terminals only)

>COLOR{DPT#}bred white underscore
Colourises "DPT=FOO in white wit red background and sets underscore (next whitespace will reset the color/underscore to normal)
In detail the # separates the colouriser from the keyword to be searched.
In other words, "DPT" is the trigger to  colourise the string starting at "DPT" up to next whitespace,
so value pairs are treated dynamically.

Colourising will do its job pretty much _after_ any replacement.

logTail understands the following aliases of AnsiEsc Colours
Foreground:
>black red green yellow blue magenta cyan white 
Background:
>bblack bred bgreen byellow bblue bmagenta bcyan bwhite 
specials:
>bold blink cright cleft cup cdown beep concealed underscore reverse



>POSTTRIGGER{firewall_AND_warning_AND_foobar}sudo /usr/sbin/beeper -f 2000 -l 100
This one does exactly what you expect. Please note that you may add an "&" to the commands...
And at this point, hopefully the modern SoC will have a beeper in future again... :)
>POSTTRIGGER{firewall}sudo /root/bin/firewall.sh _LINE_ 
will evaluate _LINE_ as the actual logline, so you may pass it as parameter

###Note
Everything works on-the-fly, your logs won't be touched at all.
Even though you are using -c(atenate) a single file 

Another option is to "send" a "Replace-command" via the origin log.
You may use something like "logger" on remote machines.
Any "important" string which changes in a regular manner e.g. an dynamic IP,
which you want to be replaced/and colorised.
e.g. your external dynamic IP should be highlighted or replaced with ppp or similar.

### REMOTE commands via "log":

1) LOGTAILREPLACE x WITH y
When logTail recognises (case-sensivite) "LOGTAILREPLACE foo-key WITH bar-value" in a line, it
will add/modify this on-the-fly to the list of replacements. 
These changes won't be written to the configuration,
and are dealed with as long it is not aborted or "overwritten" or *3

2) LOGTAILSTATS
Another command is "LOGTAILSTATS", which will inform about dropped lines and so on 

3)LOGTAILCLEAR
This "clears" the list of REMOTE injected REPLACEments.

Note that any "seen" remote coomand will ommit that line, instead it just
prints out internal informations.


logTail does now a very simple binary-check for existing files and 
will ignore those files which look more or less far behind a plain-text-file.


### (my) best practice:

a) Create a "logtail" directory, e.g. /var/log/messages/logtail and symlink
any "wanted" logfile in there.
logTail will now recognise new/deleted/truncated files automatically.
So just start it, link your preferred files (or remove a link) in place of the
given path  and even modify the config while it runs.
It will inform about discerned changes.

b) any syslogd could use a single logserver. syslogd(s) have
many powerful mechanisms to do so. 
Depending on what,where and how much is being logged, you could start logTail
in different ways by renaming the .py file e.g. ./logTail2.py ./logTail_kern_log.py
and so on. Ensure to give any "logTail" a different configuration file by
passing it with -f (--configgile).
Please note the option - l for single logfiles are no longer granted.

c) "start_logTail.sh" starts a instance within a screen session, which is the most
useful way which I prefer.

d) The qualitiy of rendered colours is hinging on the terminal software.
  I'm using xterm and Konsole which are very fine with ansi.

f) have fun...
