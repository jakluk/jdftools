#!/usr/bin/env python3

# The MIT License (MIT)
# 
# Copyright (c) 2015 Jakub Lukeš
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
from zipfile import *
from io import BytesIO
from ftplib import FTP
from datetime import date

SERVER = 'ftp.cisjr.cz'
SERVER_DIR = 'JDF'
SERVER_FILE = 'JDF.zip'
MODIFY_FILE = 'JDFmodify.txt'
DATA_DIR = 'data'
OUT_DIR = 'out'

# Parse JDF file
def jdfread(name, compulsory=0):
  lines = []
  try:
    with z.open(name + '.txt') as f:
      for line in f:
        # Parse CSV and strip from delimiters
        line = line.decode('cp1250').split('","')
        line[0] = line[0][1:]
        if len(line) == 1:
          line[0] = line[0][:-4]
        else:
          line[len(line)-1] = line[len(line)-1][:-4]
        lines.append(line)
  except KeyError:
    if compulsory == 1:
      print('Compulsory file {0} in archive {1} is missing!'.format(name, zip))
    else:
      pass
  return lines

def jdfwrite(name, content):
  if not os.path.exists('{0}/{1}'.format(DATA_DIR, OUT_DIR)):
    os.makedirs('{0}/{1}'.format(DATA_DIR, OUT_DIR))
  with open('{0}/{1}/{2}.txt'.format(DATA_DIR, OUT_DIR, name), 'w') as f:
    for l in content:
      for c in l:
        f.write('"' + c + '"')
        if c != l[len(l)-1]:
          f.write(',')
      f.write(';\r\n')

# Check whether we have the newest JDF.zip
print('Connecting to {0}'.format(SERVER))
ftp = FTP(SERVER)
ftp.login()
ftp.cwd(SERVER_DIR)
modify = int(ftp.sendcmd('MDTM ' + SERVER_FILE).split(' ')[1])
localModify = 0
try:
  with open('{0}/{1}'.format(DATA_DIR, MODIFY_FILE), 'r') as f:
    try:
      localModify = int(f.read())
    except ValueError:
      pass
except FileNotFoundError:
  pass

try:
  with open('{0}/{1}'.format(DATA_DIR, SERVER_FILE), 'r') as f:
    pass
except FileNotFoundError:
  localModify = 0

if modify > localModify:
  with open('{0}/{1}'.format(DATA_DIR, MODIFY_FILE), 'w') as f:
    print('Found newer version, downloading...')
    with open('{0}/{1}'.format(DATA_DIR, SERVER_FILE), 'wb') as file:
      ftp.retrbinary('RETR ' + SERVER_FILE, file.write)
    f.write(str(modify))
    print('Done.')
else:
  print('Current version {0} is up to date'.format(localModify))

ftp.quit()
print()

print('Starting file processing...')
zips = []
n_verzejdf = [['1.11', '', '', '', date.today().strftime('%d%m%Y'), 'Autobusy 2015']]
n_zastavky = []
n_oznacniky = []
n_dopravci = []
n_linky = []
n_linext = []
n_zaslinky = []
n_spoje = []
n_spojskup = []
n_zasspoje = []
n_udaje = []
n_kody = ['X', '+', '1', '2', '3', '4', '5', '6', '7', 'R', '#', '|', '<', '@', '%', 'W', 'w', 'x', '~', 'I', '(', ')', '$', '{', '}', '[', 'O', 'v', 's', '§', 'A', 'B', 'C', 'T', '!', 't', 'b', 'U', 'S', 'J', 'P']
n_pevnykod = []
n_caskody = []
n_navaznosti = []
n_altdop = []
n_altlinky = []
n_mistenky = []

for i in range(len(n_kody)):
  n_pevnykod.append([str(i+1), n_kody[i], ''])

with ZipFile('{0}/{1}'.format(DATA_DIR, SERVER_FILE), 'r') as main:
  # Iterate through ZIPs inside JDF.zip
  zips = sorted(main.namelist(), key = lambda x: int(x.split('.')[0]))
#  zips = [str(x)+'.zip' for x in range(1, 100)]
  for zip in zips:
    with main.open(zip) as batch:
      zdata = BytesIO(batch.read())
      with ZipFile(zdata, 'r') as z:
        # Get JDF version of current batch
        verzejdf = jdfread('VerzeJDF', 1)[0]
        version = int(verzejdf[0].split('.')[1]) # can be 8, 9, 10 or 11 (JDF version 1.X)
        
        zastavky = jdfread('Zastavky', 1)
        dopravci = jdfread('Dopravci', 1)
        linky = jdfread('Linky', 1)
        zaslinky = jdfread('Zaslinky', 1)
        spoje = jdfread('Spoje', 1)
        zasspoje = jdfread('Zasspoje', 1)
        pevnykod = jdfread('Pevnykod', 1)
        caskody = jdfread('Caskody', 1)
        
        # Optional files
        oznacniky = jdfread('Oznacniky')
        linext = jdfread('LinExt')
        spojskup = jdfread('SpojSkup')
        udaje = jdfread('Udaje')
        navaznosti = jdfread('Navaznosti')
        altdop = jdfread('Altdop')
        altlinky = jdfread('Altlinky')
        mistenky = jdfread('Mistenky')

        for d in dopravci:
          if version < 10:
            d.append('1')
          # search for unique company IDs
          if not any(d[0] in sub for sub in n_dopravci):
            n_dopravci.append(d)
          # if it's not unique, check for duplicity and assign secondary ID
          elif not any(d[2] in sub and d[5] in sub and d[6] in sub for sub in n_dopravci):
            sameId = [x for x in n_dopravci if x[0] == d[0]]
            d[12] = str(max(int(x[12]) for x in sameId) + 1)
            n_dopravci.append(d)


print('Writing final data')
jdfwrite('VerzeJDF', n_verzejdf)
#jdfwrite('Zastavky', n_zastavky)
#jdfwrite('Oznacniky', n_oznacniky)
jdfwrite('Dopravci', n_dopravci)
#jdfwrite('Linky', n_linky)
#jdfwrite('LinExt', n_linext)
#jdfwrite('Zaslinky', n_zaslinky)
#jdfwrite('Spoje', n_spoje)
#jdfwrite('SpojSkup', n_spojskup)
#jdfwrite('Zasspoje', n_zasspoje)
#jdfwrite('Udaje', n_udaje)
jdfwrite('Pevnykod', n_pevnykod)
#jdfwrite('Caskody', n_caskody)
#jdfwrite('Navaznosti', n_navaznosti)
#jdfwrite('Altdop', n_altdop)
#jdfwrite('Altlinky', n_altlinky)
#jdfwrite('Mistenky', n_mistenky)
