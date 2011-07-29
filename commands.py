from copy import deepcopy

class Command(object):
    def run(self, game, *a): pass
    def repr(self, game): pass
    def undo(self, game): pass

###############################################################################
# General commands

class UndoCommand(Command):
    sig = "undo"
    doc = "Undoes the last command you gave."
    def run(self, game):
        transparent = True
        while transparent:
            transparent = game.undoStack.pop().undo(game)
    def repr(self, game):
        pass
    def undo(self, game):
        return True # transparent

class ExitCommand(Command):
    sig = "quit"
    doc = "Exits the game, but you won't do that, right?"
    def run(self, game):
        return True

class PrintReportCommand(Command):
    sig = "print"
    doc = "Prints a report of the current game state."
    def run(self, game):
        print "=========="
        print "The map has the connections:", game.links
        print "Economy:"
        for p, g_b_s in enumerate(zip(game.gold,game.bonds,game.soldiers)):
            print "    Player %d has %d gold, %d in bonds and %d soldiers" % g_b_s
        print "Banks return rate is %.1f%%" % (game.returnRate*100)
        if game.inbattle:
            print "We're currently planning a battle"
        else: print "No battle is currently being planned"
        print "=========="
    def undo(self, game):
        return True

class HelpCommand(Command):
    sig = "help"
    doc = "Prints this help section"
    def run(self, game):
        print "=========="
        print "The help you need from people who love you,"
        for Cmd in Command.__subclasses__():
            print "    `%s`: \t%s" % (Cmd.sig, Cmd.doc)
        print "=========="

###############################################################################
# Initial commands

class LoadMapCommand(Command):
    sig = "lma"
    doc = "Loads a new map. `lma [[1],[0]]` creates a map where country 0 is connected to country 1 and country 1 is connected to country 0. All contries always have sea access."
    def run(self, game, *a):
        self.backup = game.links
        exec "game.links = " + " ".join(a)
    def repr(self, game):
        return "%s %r" % (self.sig, game.links)
    def undo(self, game):
        assert hasattr(self,"backup"), "Must run 'run' before 'undo'"
        game.links = self.backup

###############################################################################
# Economy

class SetGoldCommand(Command):
    sig = "sgo"
    doc = "Sets the gold of a player to a specific integer value"
    def run(self, game, *a):
        self.backup = (a[0], game.gold[a[0]])
        game.gold[a[0]] = int(a[1])
    def repr(self, game):
        return "\n".join("%s %d %d" % (sig, i, g)
                         for i, g in enumerate(game.gold))
    def undo(self, game):
        game.gold[self.backup[0]] = self.backup[1]

# TODO: Laas obligationer i en periode og giv rente
class SetBondsCommand(Command):
    sig = "sbs"
    doc = "Sets the current bond holdings of a player to a specific integer value"
    def run(self, game, *a):
        self.backup = (a[0], game.bonds[a[0]])
        game.bonds[a[0]] = int(a[1])
    def repr(self, game):
        return "\n".join("%s %d %d" % (sig, i, g)
                         for i, g in enumerate(game.bonds))
    def undo(self, game):
        game.bonds[self.backup[0]] = self.backup[1]

class SetSoldiersCommand(Command):
    sig = "sss"
    doc = "Sets the number of soldiers for a player to a specific integer value"
    def run(self, game, *a):
        self.backup = (a[0], game.soldiers[a[0]])
        game.soldiers[a[0]] = int(a[1])
    def repr(self, game):
        return "\n".join("%s %d %d" % (sig, i, g)
                         for i, g in enumerate(game.soldiers))
    def undo(self, game):
        game.soldiers[self.backup[0]] = self.backup[1]

class TransferCommand(Command):
    sig = "tra"
    doc = "Transfers from player a to b, x gold"
    def run(self, game, a, b, x):
        if game.gold[a] < x:
            print "Error: Player %d has only %d gold" % (a, game.gold[a])
            self.backup = None
        else:
            game.gold[a] -= x
            game.gold[b] += x
            self.backup = (a, b, x)
    def undo(self, game):
        if not self.backup:
            return True
        a, b, x = self.backup
        game.gold[a] += x
        game.gold[b] -= x

class SetReturnRateCommand(Command):
    sig = "srr"
    doc = "Set the return rate for bonds to a floting point number, like 0.1 for 10%"
    def run(self, game, rate):
        self.backup = game.returnRate
        game.returnRate = float(rate)
    def repr(self, game):
        return "%s %r" % (self.sig, game.returnRate)
    def undo(self, game):
        game.returnRate = self.backup

class BuyCommand(Command):
    sig = "buy"
    doc = "Convenient method for letting player a buy x soldiers for price 1"
    def run(self, game, a, x):
        if game.gold[a] < x:
            print "Error: Player %d has only %d gold" % (a, game.gold[a])
            self.backup = None
        else:
            game.gold[a] -= x
            game.soldiers[a] += x
            self.backup = (a, x)
    def undo(self, game):
        if not self.backup:
            return True
        a, x = self.backup
        game.soldiers[a] -= x
        game.gold[a] += x

class InvestCommand(Command):
    sig = "inv"
    doc = "

