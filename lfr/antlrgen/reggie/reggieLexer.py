# Generated from ./reggie.g4 by ANTLR 4.10.1
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
    from typing import TextIO
else:
    from typing.io import TextIO


def serializedATN():
    return [
        4,0,19,129,6,-1,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,
        2,6,7,6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,
        13,7,13,2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,
        19,2,20,7,20,2,21,7,21,2,22,7,22,1,0,1,0,1,1,1,1,1,2,1,2,1,3,1,3,
        1,4,1,4,1,5,1,5,1,6,1,6,1,7,1,7,1,8,1,8,1,9,1,9,1,10,1,10,1,11,1,
        11,1,11,1,12,1,12,1,12,1,12,1,13,1,13,5,13,79,8,13,10,13,12,13,82,
        9,13,1,14,1,14,1,15,4,15,87,8,15,11,15,12,15,88,1,15,1,15,1,16,4,
        16,94,8,16,11,16,12,16,95,1,16,1,16,1,17,4,17,101,8,17,11,17,12,
        17,102,1,18,1,18,1,18,5,18,108,8,18,10,18,12,18,111,9,18,1,18,1,
        18,1,19,1,19,1,20,1,20,1,20,1,20,1,20,1,20,1,21,1,21,1,21,3,21,126,
        8,21,1,22,1,22,0,0,23,1,1,3,2,5,3,7,4,9,5,11,6,13,7,15,8,17,9,19,
        10,21,11,23,12,25,13,27,14,29,15,31,16,33,17,35,18,37,19,39,0,41,
        0,43,0,45,0,1,0,8,3,0,65,90,95,95,97,122,4,0,48,57,65,90,95,95,97,
        122,2,0,9,9,32,32,2,0,10,10,13,13,1,0,48,57,3,0,48,57,65,70,97,102,
        8,0,34,34,47,47,92,92,98,98,102,102,110,110,114,114,116,116,3,0,
        0,31,34,34,92,92,131,0,1,1,0,0,0,0,3,1,0,0,0,0,5,1,0,0,0,0,7,1,0,
        0,0,0,9,1,0,0,0,0,11,1,0,0,0,0,13,1,0,0,0,0,15,1,0,0,0,0,17,1,0,
        0,0,0,19,1,0,0,0,0,21,1,0,0,0,0,23,1,0,0,0,0,25,1,0,0,0,0,27,1,0,
        0,0,0,29,1,0,0,0,0,31,1,0,0,0,0,33,1,0,0,0,0,35,1,0,0,0,0,37,1,0,
        0,0,1,47,1,0,0,0,3,49,1,0,0,0,5,51,1,0,0,0,7,53,1,0,0,0,9,55,1,0,
        0,0,11,57,1,0,0,0,13,59,1,0,0,0,15,61,1,0,0,0,17,63,1,0,0,0,19,65,
        1,0,0,0,21,67,1,0,0,0,23,69,1,0,0,0,25,72,1,0,0,0,27,76,1,0,0,0,
        29,83,1,0,0,0,31,86,1,0,0,0,33,93,1,0,0,0,35,100,1,0,0,0,37,104,
        1,0,0,0,39,114,1,0,0,0,41,116,1,0,0,0,43,122,1,0,0,0,45,127,1,0,
        0,0,47,48,5,123,0,0,48,2,1,0,0,0,49,50,5,44,0,0,50,4,1,0,0,0,51,
        52,5,125,0,0,52,6,1,0,0,0,53,54,5,40,0,0,54,8,1,0,0,0,55,56,5,41,
        0,0,56,10,1,0,0,0,57,58,5,58,0,0,58,12,1,0,0,0,59,60,5,91,0,0,60,
        14,1,0,0,0,61,62,5,93,0,0,62,16,1,0,0,0,63,64,5,42,0,0,64,18,1,0,
        0,0,65,66,5,43,0,0,66,20,1,0,0,0,67,68,5,124,0,0,68,22,1,0,0,0,69,
        70,5,45,0,0,70,71,5,62,0,0,71,24,1,0,0,0,72,73,5,60,0,0,73,74,5,
        45,0,0,74,75,5,62,0,0,75,26,1,0,0,0,76,80,7,0,0,0,77,79,7,1,0,0,
        78,77,1,0,0,0,79,82,1,0,0,0,80,78,1,0,0,0,80,81,1,0,0,0,81,28,1,
        0,0,0,82,80,1,0,0,0,83,84,5,63,0,0,84,30,1,0,0,0,85,87,7,2,0,0,86,
        85,1,0,0,0,87,88,1,0,0,0,88,86,1,0,0,0,88,89,1,0,0,0,89,90,1,0,0,
        0,90,91,6,15,0,0,91,32,1,0,0,0,92,94,7,3,0,0,93,92,1,0,0,0,94,95,
        1,0,0,0,95,93,1,0,0,0,95,96,1,0,0,0,96,97,1,0,0,0,97,98,6,16,0,0,
        98,34,1,0,0,0,99,101,7,4,0,0,100,99,1,0,0,0,101,102,1,0,0,0,102,
        100,1,0,0,0,102,103,1,0,0,0,103,36,1,0,0,0,104,109,5,34,0,0,105,
        108,3,43,21,0,106,108,3,45,22,0,107,105,1,0,0,0,107,106,1,0,0,0,
        108,111,1,0,0,0,109,107,1,0,0,0,109,110,1,0,0,0,110,112,1,0,0,0,
        111,109,1,0,0,0,112,113,5,34,0,0,113,38,1,0,0,0,114,115,7,5,0,0,
        115,40,1,0,0,0,116,117,5,117,0,0,117,118,3,39,19,0,118,119,3,39,
        19,0,119,120,3,39,19,0,120,121,3,39,19,0,121,42,1,0,0,0,122,125,
        5,92,0,0,123,126,7,6,0,0,124,126,3,41,20,0,125,123,1,0,0,0,125,124,
        1,0,0,0,126,44,1,0,0,0,127,128,8,7,0,0,128,46,1,0,0,0,8,0,80,88,
        95,102,107,109,125,1,6,0,0
    ]

class reggieLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    T__0 = 1
    T__1 = 2
    T__2 = 3
    T__3 = 4
    T__4 = 5
    T__5 = 6
    T__6 = 7
    T__7 = 8
    T__8 = 9
    T__9 = 10
    T__10 = 11
    T__11 = 12
    T__12 = 13
    ID = 14
    QUESTIONMARK_WILDCARD = 15
    WS = 16
    NL = 17
    INT = 18
    STRING = 19

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'{'", "','", "'}'", "'('", "')'", "':'", "'['", "']'", "'*'", 
            "'+'", "'|'", "'->'", "'<->'", "'?'" ]

    symbolicNames = [ "<INVALID>",
            "ID", "QUESTIONMARK_WILDCARD", "WS", "NL", "INT", "STRING" ]

    ruleNames = [ "T__0", "T__1", "T__2", "T__3", "T__4", "T__5", "T__6", 
                  "T__7", "T__8", "T__9", "T__10", "T__11", "T__12", "ID", 
                  "QUESTIONMARK_WILDCARD", "WS", "NL", "INT", "STRING", 
                  "HEX", "UNICODE", "ESC", "SAFECODEPOINT" ]

    grammarFileName = "reggie.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.10.1")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


