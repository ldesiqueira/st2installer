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
total_lines = 120
line_pause = 1
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
  sys.stdout.write("%s\n" % sb)
  time.sleep(line_pause)
sys.stdout.write('DONE')
