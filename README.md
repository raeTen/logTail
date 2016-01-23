#logTail 
####V 0.9.5
is a small qick and dirty python log colourisation-tool which helps observing 
unix-style log files. It has several capabilities.
Unices ONLY for now and then - since I won't deal with fairytale-logging

[X]VERSION 0.9.4 remastered
[X] VERSION 0.9.5 redesigned
[ ] VERSION 0.9.6 will have fixed issues with timing

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

logTail also drops same lines in order, after REPLACEing the replacement-keywords similar to any syslogd.
There's a "sensivity" (-s) for that. Default is 2. This means, logTail will say "repeated message"
when a maximum of 2 characters were different. Assigning -s 0 means, the lines have to be exactly 
the same to be dropped.

Whitespaces within configuration are NOT ignored and additionally 
everything is case-sensitive - unices-style.

logTail now has a simple status line and any modification could be toogled on|off by
pressing

>m(essage repeated)

>d(dropped)

>r(replace)

>c(olourised)

>t(riggered)

>h(ighlighted)

>p(ause)

Here are samples of what you can do within the configuration.

### DROP

>DROP{ FOObar}

Lines with " FOObar " would be - you guess it - dropped  while " foobar " won't

>_AND_ 

does a logical AND on the given keywords

>DROP{Foo_AND_ bar}

Lines like "Something Foo somethingelse bar " are dropped (watch the whitespaces!)

### REPLACE

>REPLACE{ fooBaR }FooBAR

just replaces words (incl. whitespaces!) in a log line so
" fooBaR " results in "fooBAR"
while

>REPLACE{ fooBaR } FooBAR 


" fooBaR " results in " fooBAR "


>REPLACE{DPT#}

This one will replace DPT=22 with nothing. 

The "#" means: Looking for >DPT< and the following up to the next >whitespace< 
and even after REPLACE you might COLORise those strings.


Replacing doesn't work in dropped lines of course.

### COLOR

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

### POSTTRIGGER

>POSTTRIGGER{firewall_AND_warning_AND_foobar}sudo /usr/sbin/beeper -f 2000 -l 100

This one does exactly what you expect. Please note that you may add an "&" to the commands...
And at this point, hopefully the modern SoC will have a beeper in future again... :)

>POSTTRIGGER{firewall}sudo /root/bin/firewall.sh _LINE_ 

>POSTTRIGGER{firewall}sudo /root/bin/firewall.sh _OLINE_ 

will evaluate _LINE_ to the actual logline (after logTail replace/colorise) logline, 
_OLINE_ as the origin logline respectively.
So logTail passes them as _one_ single parameter.

It's like:

>/root/bin/test.sh "the (origin) log line complete" 

but _not_

>/root/bin/test.sh the (origin) log line complete

You might give additional real parameters to POSTTRIGGER, but _(O)LINE_ renders to "the logline" as one parameter
Be careful with _LINE_ because it might call some externals which logs the TRIGGER-Keyword again, and that will
end up with a deadloop
###Note

Everything works on-the-fly, your logs won't be touched at all.
Even though while -c(atenate) a single file 

Another option is to "send" a "Replace-command" via the origin log.
You may use something like "logger" on remote machines.
Any "important" string which changes in a regular manner e.g. an dynamic IP,
which you want to be replaced/and colorised.
e.g. your external dynamic IP should be highlighted or replaced with ppp or similar.

#### REMOTE commands via "log":

1) LOGTAILREPLACE x WITH y

When logTail recognises (case-sensivite) "LOGTAILREPLACE foo-key WITH bar-value" in a line, it
will add/modify this on-the-fly to the list of replacements. 
These changes won't be written to the configuration,
and are dealed with as long it is not aborted or "overwritten" or *3

2 )LOGTAILCLEAR

This "clears" the list of REMOTE injected REPLACEments only.

Note that any "seen" remote coomand will ommit that line, instead it just
prints out internal informations.

### HIGHLIGHT

>HIGHLIGHT{foo_AND_bar}

this is done *after* REPLACE and COLOURISE
It simply underscores the complete log-line on matches

### Binary Log Files

Are not supported since they will mess up your terminal ;-)

logTail tries to verify a non-binary logfile by a simple check and
will ignore files which don't look like what we call plain-text-file.
Maybe switched off bei passing -b 0


### (my) best practice:

a) Create a "logtail" directory, e.g. /var/log/messages/logtail and symlink
any "wanted" logfile in there.
logTail will now recognise new/deleted/truncated files automatically.
So just start it, link your preferred files (or remove a link) in place of the
given path. There's even no reason to restart for modifications within in configuration files
It will inform about discerned changes.

b) any syslogd* could use a single logserver. syslogd(s) have
many powerful mechanisms to do so. 
Depending on what,where and how much is being logged, you could start logTail
in different ways by renaming the .py file e.g. ./logTail2.py ./logTail_kern_log.py
and so on. Each with a different configuration file by
passing it with -f (--configfile).

Please note: the option - l for single logfiles is not longer granted.

c) "start_logTail.sh" starts a instance within a screen session, which is the most
useful way which I prefer.

d) The qualitiy of rendered colours is hinging on the terminal software.
  I'm using xterm and Konsole which are very fine with ansi.
  Maybe I'll play around with 256color ansi someday

f) have fun...
