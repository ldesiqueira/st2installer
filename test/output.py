#!/usr/bin/python

import sys, random, time

# A sample app for UI testing that just throws some output to stdout and stderr.

# First we need to make sure the output is composed of 
# some great, meaningful words.
dictionary = [
  'automation', 'openstack', 'big data', 'cloud-based',
  'disruptive', 'innovation', 'petabyte', 'scalable',
  'gamificaton', 'synergy', 'enterprise', 'data-driven',
  'crowdsourcing', 'real-time', 'pivot', 'remediation' 
]

# Parameters for total runtime, warning/error frequency (every N lines).
warning_frequency = 5
error_frequency = 9
total_lines = 100
line_pause = 0.5
word_count = 4

# Throw random lines.

for line in range(total_lines):
  sb = ''
  if line>0 and not (line % warning_frequency):
    sb += 'WARNING: '
  elif line>0 and not (line % error_frequency):
    sb += 'ERROR: '
  for word in range(word_count):
    sb += '%s ' % random.choice(dictionary)
  if line>0 and not (line % (total_lines/5)):
    sys.stdout.write("PROGRESS: %i\n" % (100/float(total_lines)*line))
  sys.stdout.write("%s\n" % sb)
  sys.stdout.flush()
  time.sleep(line_pause)
