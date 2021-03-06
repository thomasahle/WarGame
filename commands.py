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
    doc = "Prints a report of the current game state. If called with an argument p, it prints only the state of that player."
    def run(self, game, *args):
        if len(args) == 1:
            players = [int(args[0])]
        else: players = range(game.players)
        print "=========="
        print "The map has the connections:", game.links
        print "Economy:"
        for p in players:
            print "    Player %d has %d gold and %d soldiers" % (p, game.gold[p], game.soldiers[p])
            print "    His/her bonds are %r" % [bond[1:] for bond in game.bonds if bond[0]==p]
        if game.inbattle:
            print "Currently on the supportStack:"
            print "    " + " ".join(map(repr,game.supportStack))
            print "Currently on the attackStack:"
            print "    " + " ".join(map(repr,game.attackStack))
        else:
            print "No battles are currently being planned"
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
        while len(game.gold) < game.players:
            game.gold.append(0)
        while len(game.soldiers) < game.players:
            game.soldiers.append(0)
        while len(game.links) < game.players:
            game.links.append([])
    def repr(self, game):
        return "%s %s" % (self.sig, game.players)
    def undo(self, game):
        game.players = self.backup
    
class SetMapCommand(Command):
    sig = "sma"
    doc = "Sets a new map. Example: `sma [[1],[0]]` creates a map where " +\
          "country 0 is connected to country 1 and country 1 is connected " +\
          "to country 0. All contries always have sea access."
    def run(self, game, *a):
        links = json.loads(" ".join(a))
        if len(links) < game.players:
            print "Error: each %d players must have a (possibly empty) sublist." % game.players
            self.backup = None
        else:
            for p, cons in enumerate(links):
                for q in cons:
                    if not p in links[q]:
                        print "Error: Links (for player %d) must be symetrical." % p
                        self.backup = None
                        return
            self.backup = game.links
            game.links = links
    def repr(self, game):
        return "%s %r" % (self.sig, game.links)
    def undo(self, game):
        if not self.backup:
            return True
        game.links = self.backup

###############################################################################
# Economy commands

class RunEconomyCommand(Command):
    sig = "rec"
    doc = "Make a step in the economy, sending returns from bonds."
    def run(self, game):
        self.backup = deepcopy((game.gold, game.bonds))
        newList = set()
        for player, amount, lockedRounds, rate in game.bonds:
            game.gold[player] += int(amount * rate/100.)
            print "Info: Player %d got %d earnings from a bond." % (player, int(amount * rate/100.))
            if lockedRounds == 1:
                game.gold[player] += amount
                print "Info: Released a bond of value %d to player %d." % (amount, player)
            else:
                newList.add((player, amount, lockedRounds-1, rate))
        game.bonds = newList
    def undo(self, game):
        game.gold, game.bonds = self.backup

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

class SetAllGoldCommand(Command):
    sig = "sag"
    doc = "Set the gold of every player to n"
    def run(self, game, n):
        self.backup = deepcopy(game.gold)
        game.gold = [int(n)]*game.players
    def undo(self, game):
        game.gold = self.backup

class SetBondsCommand(Command):
    sig = "sbs"
    doc = "Sets the current bond holdings of a player as a list [[amount, rate, lockedRounds]], where rate is a the roundly return rate in percent"
    def run(self, game, a, *bonds):
        a = int(a)
        self.backup = deepcopy(game.bonds)
        bonds = json.loads(" ".join(bonds))
        bonds = set((a,)+tuple(bond) for bond in bonds)
        game.bonds.update(bonds)
    def repr(self, game):
        lines = []
        for i in range(game.players):
            lines.append("%s %d %r" % (self.sig, i,
                    [list(bond[1:]) for bond in game.bonds if bond[0] == i]))
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
        if n < 0:
            print "Error: n must by >= 0. Soldiers can't be sold."
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
        a, n, k, y = int(a), int(n), int(k), int(y)
        if n <= 0:
            print "Error: n must be > 0. To retract, use `ret`."
            self.backup = None
        elif game.gold[a] < n:
            print "Error: Player %d has only %d gold" % (a, game.gold[a])
            self.backup = None
        else:
            game.gold[a] -= n
            bond = (a, n, k, y)
            game.bonds.add(bond)
            self.backup = bond
            print "Info: Created bond of %d for player %d at rate %d%%. Locked for %d rounds." \
                  % (bond[1], bond[0], bond[3], bond[2])
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

###############################################################################
# Battle commands

class SetWaterDiePercentage(Command):
    sig = "swd"
    doc = "Sets the percentage of soldiers that die in an overseas battle."
    def run(self, game, p):
        self.backup = game.waterDiePercentage
        game.waterDiePercentage = int(p)
    def repr(self, game):
        return "%s %d" % (self.sig, game.waterDiePercentage)
    def undo(self, game):
        game.waterDiePercentage = self.backup

class NewBattleCommand(Command):
    sig = "nba"
    doc = "Starts a new battle session"
    def run(self, game):
        if game.supportStack or game.attackStack or game.inbattle:
            print "Warning: You already had a battle going." +\
                  " If you wanted it, undo this and use `rba` to execute it."
            self.backup = None
        else:
            self.backup = deepcopy((game.supportStack, game.attackStack, game.inbattle))
            game.inbattle = True
            del game.supportStack[:]
            del game.attackStack[:]
    def repr(self, game):
        if game.inbattle:
            return self.sig
    def undo(self, game):
        game.supportStack, game.attackStack, game.inbattle = self.backup

class SupportCommand(Command):
    sig = "sup"
    doc = "Player a chooses to support player b during the next battle."
    def run(self, game, a, b):
        a, b = int(a), int(b)
        if not game.inbattle:
            print "Error: Not currently in a battle."
            self.backup = None
        elif a in (p for p,q in game.attackStack):
            print "Error: Player %d is already on the attackStack." % a
            self.backup = None
        elif a in (p for p,q in game.supportStack):
            print "Error: Player %d is already on the supportStack." % a
            self.backup = None
        elif game.soldiers[a] == 0:
            print "Error: Player %d has no soldiers." % a
            self.backup = None
        else:
            game.supportStack.append((a,b))
            self.backup = (a,b)
    def repr(self, game):
        return "\n".join("%s %d %d" % (self.sig, a, b) for a,b in game.supportStack)
    def undo(self, game):
        if not self.backup:
            return True
        game.supportStack.remove(self.backup)

class AttackCommand(Command):
    sig = "att"
    doc = "Player a chooses to attack player b during the next battle."
    def run(self, game, a, b):
        a, b = int(a), int(b)
        if not game.inbattle:
            print "Error: Not currently in a battle."
            self.backup = None
        elif a in (p for p,q in game.attackStack):
            print "Error: Player %d is already on the attackStack." % a
            self.backup = None
        elif a in (p for p,q in game.supportStack):
            print "Error: Player %d is already on the supportStack." % a
            self.backup = None
        elif game.soldiers[a] == 0:
            print "Error: Player %d has no soldiers." % a
            self.backup = None
        else:
            game.attackStack.append((a,b))
            self.backup = (a,b)
    def repr(self, game):
        return "\n".join("%s %d %d" % (self.sig, a, b) for a,b in game.attackStack)
    def undo(self, game):
        if not self.backup:
            return True
        game.attackStack.remove(self.backup)

def supportDfs(game, src, dst):
    """ Returns true if src supports dst, directly or indirectly """
    cache = set()
    while src != dst:
        if src in cache:
            return False
        cache.add(src)
        for a,b in game.supportStack:
            if a == src:
                src = b
                break
    return True

def moveGold(game, oldgold, fromTeam, toTeam):
    taken = 0
    # Remove
    for p in fromTeam:
        # Take gold
        take = min(oldgold[p],game.gold[p]) // 2
        taken += take
        game.gold[p] -= take
        # Take bonds
        new = set()
        for player, amount, locked, rate in game.bonds:
            if player == p:
                new.add((player, amount-(amount//2), locked, rate))
                taken += amount//2
        game.bonds = set(bond for bond in game.bonds if bond[0] != p)
        game.bonds.update(new)
    # Give
    for p in toTeam:
        game.gold[p] += taken // len(toTeam)
    # The rest to the attacker
    game.gold[toTeam[0]] += taken % len(toTeam)
    print "Info: The winning team stole %d in gold and bonds" % taken

def takeSoldiers(game, team, n):
    total = sum(game.soldiers[p] for p in team)
    if total == 0:
        return
    remainder = n
    for p in team:
        died = int(game.soldiers[p]/float(total) * n)
        game.soldiers[p] -= died
        remainder -= died
    # The remainder by rotation
    while remainder > 0:
        for p in team:
            if remainder > 0 and game.soldiers[p] > 0:
                game.soldiers[p] -= 1
                remainder -= 1

class RunBattleCommand(Command):
    sig = "rba"
    doc = "Run the current battle session"
    def run(self, game):
        if not game.inbattle:
            print "Error: Not currently in a battle, use `nba` to start one."
            self.backup = None
            return
        self.backup = (deepcopy(game.gold), deepcopy(game.soldiers),
                       deepcopy(game.attackStack), deepcopy(game.supportStack),
                       deepcopy(game.bonds))
        oldgold = deepcopy(game.gold)
        # Init groups
        battles = []
        for a,b in game.attackStack:
            # Check merge
            for p,q in battles:
                if b == q[0]:
                    if q[0] in game.links[a]:
                        p.insert(0, a)
                    else:
                        p.append(a)
                    break
            else:
                battles.append(([a],[b]))
        # Add supporters
        for p in range(game.players):
            for atts,defs in battles:
                # Notice it is important that we check support for the defender
                # first, as there may be love/hate loops
                if supportDfs(game, p, defs[0]):
                    if p != defs[0]:
                        defs.append(p)
                elif any(supportDfs(game, p, at) for at in atts):
                    if p not in atts:
                        atts.append(p)
        # Sort battles by biggest army
        battles.sort(key = lambda (atts,defs): -game.soldiers[atts[0]])
        # Run battles
        for atts,defs in battles:
            # Kill water attacking soldiers
            if defs[0] not in game.links[atts[0]]:
                before = sum(game.soldiers[p] for p in atts)
                for p in atts:
                    game.soldiers[p] = int((1-1/100.*game.waterDiePercentage) * game.soldiers[p])
                after = sum(game.soldiers[p] for p in atts)
                if before-after > 0:
                    print "Info: Team %r lost %d soldiers for attacking over water" % (atts,before-after)
            # Check armies
            aArmy = sum(game.soldiers[p] for p in atts)
            if aArmy == 0:
                print "Info: Team %r no longer has soldiers and retreat form attacking %r." % (atts, defs)
                continue
            dArmy = sum(game.soldiers[p] for p in defs)
            # Assign deads
            deads = min(aArmy, dArmy)
            takeSoldiers(game, atts, deads)
            takeSoldiers(game, defs, deads)
            if aArmy > dArmy:
                print "%r attacked %r and won" % (atts, defs)
            elif aArmy == dArmy:
                print "%r drew %r" % (atts, defs)
            else:
                print "%r attacked %r, but lost" % (atts, defs)
            print "%d soldiers died from each team." % (deads,),
            if deads > 0:
                print "They will be forever missed."
            else: print
            # Assign gold
            if aArmy > dArmy:
                moveGold(game, oldgold, defs, atts)
            elif dArmy > aArmy:
                moveGold(game, oldgold, atts, defs)
        # Clear stuff
        game.inbattle = False
        del game.attackStack[:]
        del game.supportStack[:]
    def undo(self, game):
        if not self.backup:
            return True
        game.gold, game.soldiers, game.attackStack, game.supportStack, game.bonds = self.backup
        game.inbattle = True

