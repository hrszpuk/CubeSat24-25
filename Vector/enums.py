from enum import Enum

Mode = Enum("Mode", [("TEST", 0), ("MANUAL", 1), ("AUTO", 2)])
OBDHState = Enum("OBDHState", [("INITIALISING", 0), ("READY", 1), ("IDLE", 2), ("BUSY", 3)])
Phase = Enum("Phase", [("INITIALISATION", 0), ("FIRST", 1), ("SECOND", 2), ("THIRD", 3)])
SubPhase = Enum("SubPhase", [("a", 1), ("b", 2), ("c", 3)])
TTCState = Enum("TTCState", [("INITIALISING", 0), ("READY", 1), ("CONNECTED", 2)])
MessageType = Enum("MessageType", [("LOG", 0), ("MESSAGE", 1), ("DATA", 2), ("FILEMETADATA", 3), ("FILEDATA", 4)])