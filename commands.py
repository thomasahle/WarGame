from copy import deepcopy
import json

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
        for p in range(game.players):
            print "    Player %d has %d gold and %d soldiers" % (p, game.gold[p], game.soldiers[p])
            print "    His/her bonds are %r" % [bond for bond in game.bonds if bond[0]==p]
        if game.inbattle:
            print "We're currently planning a battle"
        else: print "No battles are currently being planned"
        print "=========="
    def undo(self, game):
        return True

class HelpCommand(Command):
    sig = "help"
    doc = "Prints this help section"
    def run(self, game):
        print "=========="
        print "The help you need - from people who love you,"
        for Cmd in Command.__subclasses__():
            print "    `%s`: \t%s" % (Cmd.sig, Cmd.doc)
        print "=========="

###############################################################################
# Initial commands

class SetPlayersCommand(Command):
    sig = "sps"
    doc = "Sets the number of players in the game to a specific number."
    def run(self, game, n):
        self.backup = game.players
        game.players = int(n)
        while len(game.gold) <= game.players:
            game.gold.append(0)
        while len(game.soldiers) <= game.players:
            game.soldiers.append(0)
    def repr(self, game):
        return "%s %s" % (self.sig, game.players)
    def undo(self, game):
        game.players = self.backup
    
class LoadMapCommand(Command):
    sig = "lma"
    doc = "Loads a new map. `lma [[1],[0]]` creates a map where country 0 is connected to country 1 and country 1 is connected to country 0. All contries always have sea access."
    def run(self, game, *a):
        self.backup = game.links
        game.links = json.loads(" ".join(a))
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
    def run(self, game, a, n):
        a, n = int(a), int(n)
        self.backup = (a, game.gold[a])
        game.gold[a] = n
    def repr(self, game):
        return "\n".join("%s %d %d" % (self.sig, i, g)
                         for i, g in enumerate(game.gold))
    def undo(self, game):
        game.gold[self.backup[0]] = self.backup[1]

class SetBondsCommand(Command):
    sig = "sbs"
    doc = "Sets the current bond holdings of a player as a [[to a specific integer value"
    def run(self, game, a, *bonds):
        a = int(a)
        self.backup = deepcopy(game.bonds)
        bonds = json.loads(" ".join(bonds), locals())
        bonds = set((a,)+bond for bond in bonds)
        game.bonds += bonds
    def repr(self, game):
        lines = []
        for i in range(game.players):
            lines.append("%s %r" % (self.sig,
                    [bond[1:] for bond in game.bonds if bond[0] == i]))
        return "\n".join(lines)
    def undo(self, game):
        game.bonds = self.backup

class SetSoldiersCommand(Command):
    sig = "sss"
    doc = "Sets the number of soldiers for a player to a specific integer value"
    def run(self, game, a, n):
        a, n = int(a), int(n)
        self.backup = (a, game.soldiers[a])
        game.soldiers[a] = n
    def repr(self, game):
        return "\n".join("%s %d %d" % (self.sig, i, g)
                         for i, g in enumerate(game.soldiers))
    def undo(self, game):
        game.soldiers[self.backup[0]] = self.backup[1]

class TransferCommand(Command):
    sig = "tra"
    doc = "Transfers from player a to b, n gold"
    def run(self, game, a, b, n):
        a, b, n = int(a), int(b), int(n)
        if n <= 0:
            print "Error: Gold transfers must be positive"
            self.backup = None
        elif game.gold[a] < n:
            print "Error: Player %d has only %d gold" % (a, game.gold[a])
            self.backup = None
        else:
            game.gold[a] -= n
            game.gold[b] += n
            self.backup = (a, b, n)
    def undo(self, game):
        if not self.backup:
            return True
        a, b, n = self.backup
        game.gold[a] += n
        game.gold[b] -= n

class BuyCommand(Command):
    sig = "buy"
    doc = "Convenient method for letting player a buy n soldiers for price 1."
    def run(self, game, a, n):
        a, n = int(a), int(n)
        if n <= 0:
            print "Error: n must by > 0. Soldiers can't be sold."
            self.backup = None
        elif game.gold[a] < n:
            print "Error: Player %d has only %d gold" % (a, game.gold[a])
            self.backup = None
        else:
            game.gold[a] -= n
            game.soldiers[a] += n
            self.backup = (a, n)
    def undo(self, game):
        if not self.backup:
            return True
        a, n = self.backup
        game.soldiers[a] -= n
        game.gold[a] += n

class InvestCommand(Command):
    sig = "inv"
    doc = "Invest for player a, n gold for k rounds at rate y."
    def run(self, game, a, n, k, y):
        a, n, k, y = int(a), int(n), int(k), float(y)
        if n <= 0:
            print "Error: n must be > 0. To retract, use `ret`."
            self.backup = None
        elif game.gold[a] < n:
            print "Error: Player %d has only %d gold" % (a, game.gold[a])
            self.backup = None
        elif n < 0:
            game.gold[a] -= n
            bond = (a, n, k, y)
            game.bonds.add(bond)
            self.backup = bond
    def undo(self, game):
        if not self.backup:
            return True
        game.bonds.remove(self.backup)

class RetractCommand(Command):
    sig = "ret"
    doc = "Retract from player a's bonds, n gold for fee of k, as this breaks the round bound."
    def run(self, game, a, n, k):
        a, n, k = int(a), int(n), int(k)
        if n <= 0:
            print "Error: n must be > 0. To invest use `inv`."
            self.backup = None
            return
        available = sum(bond[1] for bond in game.bonds if bond[0]==a)
        if available < n:
            print "Error: Player %d doesn't have %d gold available. (Has %d)" \
                    % (a, n, available)
            self.backup = None
        elif game.gold[a] + available < k:
            print "Error: Player %d doesn't have enough money to pay the fee. (Has %d)" \
                    % (a, game.gold[a]+available)
            self.backup = None
        else:
            self.backup = (deepcopy(game.bonds), a, game.gold[a])
            taken = 0
            deleted = set()
            for bond in game.bonds:
                if bond[0] == a:
                    taken += bond[1]
                    deleted.add(bond)
                if taken >= n and game.gold[a]+taken >= k:
                    break
            game.bonds -= deleted
            game.gold[a] += taken
            game.gold[a] -= k
            print "Took out %d gold, gave %d to the bank. Account now has %d gold." \
                    % (taken, k, game.gold[a])
    def undo(self, game):
        if not self.backup:
            return True
        bouds, a, gold = self.backup
        game.bonds = bouds
        game.gold[a] = gold

