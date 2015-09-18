# JDFtools
A set of tools to work with data from the `Czech National Information System of Timetables` ([CIS JR](http://chaps.cz/eng/products/CIS)), provided in the JDF format. Current JDF version is 1.11, but older versions may be still used.

## jdfmerge.py

The official source provides ~10.5k zip files (batches) inside another zip. That is rather unconvenient to parse. This script tries to merge all of them into a single batch. It can also download up-to-date data from the server.

Currently outputs 4/17 files specified in the JDF 1.11:
 - [x] **VerzeJDF**
 - [x] **Zastavky**
 - [ ] Oznacniky
 - [x] **Dopravci**
 - [ ] Linky
 - [ ] LinExt
 - [ ] Zaslinky
 - [ ] Spoje
 - [ ] SpojSkup
 - [ ] Zasspoje
 - [ ] Udaje
 - [x] **Pevnykod**
 - [ ] Caskody
 - [ ] Navaznosti
 - [ ] Altdop
 - [ ] Altlinky
 - [ ] Mistenky

## Useful links

* [Source of timetable data](http://goo.gl/ILULNj)

JDF specification (in Czech):
* [version 1.9](http://chaps.cz/files/cis/jdf-1.9.pdf)
* [version 1.10](http://chaps.cz/files/cis/jdf-1.10.pdf)
* [version 1.11](http://www.mdcr.cz/NR/rdonlyres/BD24BAB6-29EC-4E03-B91D-700494A41284/0/metodickyPokyn5.pdf) (scroll down to page 16)

## Final notes

IDs may not be consistent across data updates, because they are being generated during run and I have no access to the central database. Current priority is to parse and merge all the files. Then I may focus on refactoring and creating some other tools. Also, the software works only with bus data, since parseable timetables for any other means of transport aren't currently available.
