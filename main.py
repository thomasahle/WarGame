#!/bin/env python

import sys
import commands

backup = "gameBackup.cmds"

class Game:
    players = 0
    
    links = []
    gold = []
    bonds = set() # (list of [player, amount, lockedRounds, rate])
    soldiers = []
    
    waterDiePercentage = 10
    
    inbattle = False
    attackStack = []
    supportStack = []
    
    undoStack = []
game = Game()

###############################################################################
# Commands

def runCmd(cmd):
    parts = cmd.split()
    for Cmd in commands.Command.__subclasses__():
        if Cmd.sig == parts[0]:
            inst = Cmd()
            game.undoStack.append(inst)
            return inst.run(game, *parts[1:])
    else:
        print "Unknown command: '%s'" % parts[0]
    return False

def saveState():
    f = open(backup, "w")
    for Cmd in commands.Command.__subclasses__():
        line = Cmd().repr(game)
        if line:
            print >> f, line

###############################################################################
# Run

if __name__ == "__main__":
    while True:
        try:
            cmd = raw_input("% ").strip()
        except EOFError:
            break
        if not cmd:
            continue
        try:
            isdone = runCmd(cmd)
        except:
            import sys, traceback
            traceback.print_exc()
            isdone = False
        if isdone:
            break
        saveState()
    
    print "Well played!"

