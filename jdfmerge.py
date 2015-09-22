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
SERVER_LIST_DIR = 'seznamy'
SERVER_LIST_STOPS = 'zastavky.txt'
SERVER_FILE = 'JDF.zip'
MODIFY_FILE = 'JDFmodify.txt'
DATA_DIR = 'data'
OUT_DIR = 'out'

# Parse JDF file
def jdfread(name, z, compulsory=0):
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
  try:
    content = sorted(list(content), key = lambda x: int(x[0]))
  except ValueError:
    pass
  
  if not os.path.exists('{0}/{1}'.format(DATA_DIR, OUT_DIR)):
    os.makedirs('{0}/{1}'.format(DATA_DIR, OUT_DIR))
  with open('{0}/{1}/{2}.txt'.format(DATA_DIR, OUT_DIR, name), 'w') as f:
    for l in content:
      i = 0
      for c in l:
        f.write('"' + c + '"')
        if i != len(l)-1:
          f.write(',')
        i += 1
      f.write(';\r\n')

def processZastavky():
  print('Zastavky')
  global n_zastavky
  global l_zastavky
  # Get list of all stops
  # TODO: Identify country
  with open('{0}/{1}'.format(DATA_DIR, SERVER_LIST_STOPS), 'rb') as z:
    i = 1
    for line in z:
      line = line.decode('cp1250')[:-2].split(',')
      if len(line) == 1:
        line.append('')
      if len(line) == 2:
        line.append('')
      n_zastavky.update({tuple(line):tuple([str(i)]+8*[''])})
      i += 1
  
  for zip in zips:
    batchID = zip.split('.')[0]
    with main.open(zip) as batch:
      zdata = BytesIO(batch.read())
      with ZipFile(zdata, 'r') as z:
        zastavky = jdfread('Zastavky', z, 1)
        
        for z in zastavky:
          zast = z[1].split(',')
          if len(zast) > 1:
            z[1] = zast[0]
            z[2] = zast[1]
          if len(zast) > 2:
            z[3] = zast[2]
          x = n_zastavky[tuple(z[1:4])]
          # Write with stop names keys
          n_zastavky.update({tuple(z[1:4]):tuple([x[0]]+z[4:])})
          l_zastavky.update({tuple([batchID, z[0]]):n_zastavky[tuple(z[1:4])][0]})
  # Change keys to stop ID
  n_zastavky = {str(x[1][0]):tuple(list(x[0])+list(x[1][1:])) for x in n_zastavky.items()}

def getVersion(z):
  # Get JDF version of current batch
  verzejdf = jdfread('VerzeJDF', z, 1).pop()
  return int(verzejdf[0].split('.')[1])

def processOznacniky():
  print('Oznacniky')

def processDopravci():
  print('Dopravci')
  global n_dopravci
  global l_dopravci
  # Processing carriers
  for zip in zips:
    batchID = zip.split('.')[0]
    with main.open(zip) as batch:
      zdata = BytesIO(batch.read())
      with ZipFile(zdata, 'r') as z:
        version = getVersion(z)
        dopravci = jdfread('Dopravci', z, 1)
        
        if version < 10: # add missing field in JDF <1.10
          dopravci = [x+['1'] for x in dopravci]
        # Write with keys (ICO, Address)
        n_dopravci.update({tuple([x[0]]+[x[5]]):tuple(x[1:5]+x[6:]) for x in dopravci})
        l_dopravci.update({tuple([batchID, x[0], x[5], x[-1]]):tuple() for x in dopravci})
  
  # Assign secondary ID for carriers with the same company ID (ICO)
  for d in {x for (x, y) in n_dopravci}:
    carrier = {x for x in n_dopravci.items() if x[0][0] == d}
    if len(carrier) > 1:
      for i in range(len(carrier)):
        c = carrier.pop()
        n_dopravci.update({c[0]:tuple(list(c[1][:-1])+[str(i+1)])})
    else:
      c = carrier.pop()
      n_dopravci.update({c[0]:tuple(list(c[1][:-1])+['1'])})
  
  for j in l_dopravci.items():
    d = n_dopravci[(j[0][1], j[0][2])]
    l_dopravci.update({j[0]:d[-1]})
  
  # Change keys to (ICO, Secondary ID)
  n_dopravci = {tuple([x[0][0]]+[x[1][-1]]):tuple(list(x[1][:4])+[x[0][1]]+list(x[1][4:-1])) for x in n_dopravci.items()}
  # Linker (BatchID, ICO, Original sec. ID) -> New sec. ID
  l_dopravci = {tuple([x[0][0], x[0][1], x[0][3]]):x[1] for x in l_dopravci.items()}

def processLinky():
  print('Linky')
  global n_linky
  global l_linky
  # Processing lines
  for zip in zips:
    batchID = zip.split('.')[0]
    with main.open(zip) as batch:
      zdata = BytesIO(batch.read())
      with ZipFile(zdata, 'r') as z:
        version = getVersion(z)
        linky = jdfread('Linky', z, 1)
        for l in range(len(linky)):
          # Add fields missing in older JDF versions
          if version < 10:
            linky[l] = linky[l][:4] + ['A', '0', '0', '0'] + linky[l][4:] + ['1', '1']
          if version < 11:
            linky[l] = linky[l][:8] + ['0'] + linky[l][8:]
          linky[l][15] = l_dopravci[(batchID, linky[l][2], linky[l][15])]
        # Write with keys (Line number, valid from, valid to)
        n_linky.update({tuple([x[0]]+[x[13]]+[x[14]]):tuple(list(x[1:13])+list(x[15:])) for x in linky})
        l_linky.update({tuple([batchID, x[0], x[13], x[14], x[-1]]):tuple() for x in linky})
  
  # Assign secondary ID based on timetable validity
  for l in {x for (x, y, z) in n_linky}:
    line = {x for x in n_linky.items() if x[0][0] == l}
    if len(line) > 1:
      for i in range(len(line)):
        l = line.pop()
        n_linky.update({l[0]:tuple(list(l[1][:-1])+[str(i+1)])})
    else:
      l = line.pop()
      n_linky.update({l[0]:tuple(list(l[1][:-1])+['1'])})
  
  for j in l_linky.items():
    l = n_linky[(j[0][1], j[0][2], j[0][3])]
    l_dopravci.update({j[0]:l[-1]})
  
  # Change keys to (Line number, Secondary ID)
  n_linky = {tuple([x[0][0]]+[x[1][-1]]):tuple(list(x[1][:12])+list(x[0][1:])+list(x[1][12:-1])) for x in n_linky.items()}
  # Linker (BatchID, Line number, Original sec. ID) -> New sec. ID
  l_linky = {tuple([x[0][0], x[0][1], x[0][4]]):x[1] for x in l_linky.items()}

def processLinExt():
  print('LinExt')
  
def processZaslinky():
  print('Zaslinky')

def processSpoje():
  print('Spoje')

def processSpojSkup():
  print('SpojSkup')

def processZasspoje():
  print('Zasspoje')

def processUdaje():
  print('Udaje')

def processPevnykod():
  print('Pevnykod')
  global n_pevnykod
  for i in range(len(n_kody)):
    n_pevnykod.update({str(i+1): tuple([n_kody[i], ''])})
  
def processCaskody():
  print('Caskody')

def processNavaznosti():
  print('Navaznosti')

def processAltdop():
  print('Altdop')

def processAltlinky():
  print('Altlinky')

def processMistenky():
  print('Mistenky')

def updateData():
  # Check whether we have the newest JDF.zip
  print('Connecting to {0}'.format(SERVER))
  ftp = FTP(SERVER)
  ftp.login()
  modify = int(ftp.sendcmd('MDTM {0}/{1}'.format(SERVER_DIR, SERVER_FILE)).split(' ')[1])
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
      print('Found newer version {0}, downloading...\n'.format(modify))
      with open('{0}/{1}'.format(DATA_DIR, SERVER_LIST_STOPS), 'wb') as file:
        ftp.retrbinary('RETR {0}/{1}'.format(SERVER_LIST_DIR, SERVER_LIST_STOPS), file.write)
      with open('{0}/{1}'.format(DATA_DIR, SERVER_FILE), 'wb') as file:
        ftp.retrbinary('RETR {0}/{1}'.format(SERVER_DIR, SERVER_FILE), file.write)
      f.write(str(modify))
      print('Done.')
  else:
    print('Current version {0} is up to date\n'.format(localModify))

  ftp.quit()

zips = []
n_verzejdf = [['1.11', '', '', '', date.today().strftime('%d%m%Y'), 'Autobusy 2015']]
n_zastavky = dict()
n_oznacniky = dict()
n_dopravci = dict()
n_linky = dict()
n_linext = dict()
n_zaslinky = dict()
n_spoje = dict()
n_spojskup = dict()
n_zasspoje = dict()
n_udaje = dict()
n_kody = ['X', '+', '1', '2', '3', '4', '5', '6', '7', 'R', '#', '|', '<', '@', '%', 'W', 'w', 'x', '~', 'I', '(', ')', '$', '{', '}', '[', 'O', 'v', 's', '§', 'A', 'B', 'C', 'T', '!', 't', 'b', 'U', 'S', 'J', 'P']
n_pevnykod = dict()
n_caskody = dict()
n_navaznosti = dict()
n_altdop = dict()
n_altlinky = dict()
n_mistenky = dict()

# Linkers between original and new IDs
l_zastavky = dict()
l_oznacniky = dict()
l_dopravci = dict()
l_linky = dict()
l_zaslinky = dict()
l_spoje = dict()
l_spojskup = dict()
l_zasspoje = dict()
l_pevnykod = dict()

updateData();

# File processing
print('Starting file processing...')

with ZipFile('{0}/{1}'.format(DATA_DIR, SERVER_FILE), 'r') as main:
  # Iterate through ZIPs inside JDF.zip
  zips = sorted(main.namelist(), key = lambda x: int(x.split('.')[0]))
  #zips = [str(x)+'.zip' for x in range(1, 100)]
  
  processPevnykod()
  processDopravci()
  processZastavky()
  processLinky()
  

# Final data export
print('\nWriting final data')

n_pevnykod = [[x[0]]+list(x[1]) for x in n_pevnykod.items()]
n_zastavky = [[x[0]]+list(x[1]) for x in n_zastavky.items()]
n_dopravci = [[x[0][0]]+list(x[1])+[x[0][1]] for x in n_dopravci.items()]
n_linky    = [[x[0][0]]+list(x[1])+[x[0][1]] for x in n_linky.items()]

jdfwrite('VerzeJDF', n_verzejdf)
jdfwrite('Zastavky', n_zastavky)
#jdfwrite('Oznacniky', n_oznacniky)
jdfwrite('Dopravci', n_dopravci)
jdfwrite('Linky', n_linky)
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

print('Done, exiting.')
