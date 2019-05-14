# RoboVac-Workbench
Scripts used to reverse-engineer the Eufy RoboVac 11c protocol

## requirements.txt
Python package requirements for any scripts in the repository. It's easiest to install these in a Virtualenv and work
from there.

## Protocol
Files and scripts used to reverse-engineer the protocol itself, including Protobuf definitions.

## demo.py
A simple Python script that demos how to execute different actions on your Robovac. Remember to fill in the
appropriate device IP and device local code.

### Local code
Each Eufy RoboVac seems to have a unique local code. The easiest way to find it is to run logcat over ADB while
running the Eufy app and performing a few actions. You can then grep for a string like "localCode" - it should be a
16 character code.

## Tools used
[pbtk](https://github.com/marin-m/pbtk) used to reverse engineer proto definitions from compiled Protobuf files. 

[jadx](https://github.com/skylot/jadx) used to decompile the Eufy Home app and analyse how it interacts with the RoboVac.

## Acknowledgements
Thanks to @mjg59's work on decrypting packets from Eufy devices. See it in action here: [google/python-lakeside](https://github.com/google/python-lakeside)