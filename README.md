# Overview
We want to build a "Hackers"-style virtual environment to represent the March Hare inside Cyberez's infrastructure. The players will explore and defend Cyberez by exploring this virtual environment (the MUD). Just like in a traditional MUD, the players will need to go to different locations and solve specific puzzles to get items, which they will then use in other locations to solve other puzzles. In addition to the MUD environment, we will also expose the ability for players to apply real-world technical skills to influence the game: there will be one or more EC2 instances that the players need to configure or attack (CTF-style) to unlock more in-MUD puzzles.

The scope of the boss fight is that the players were invited in to Cyberez's infrastructure by the new CISO and quickly discovered a distributed service running on many hosts that presented itself as a MUD. Since the March Hare learned from the Deckers, who are all about hacker pop culture, it has latched on to those ideas like a child and built itself around those concepts. The end goal is for the players to cut off the link between the March Hare and the virtual world/persistence system. As a secret bonus/easter egg, the players can also cut off the link between the March Hare and the Daemon, if they notice it.

The actual puzzles have yet to be designed (one of the tasks!), but you could imagine a flow something like: steal a cryptochip from Playtronics (Sneakers), dodge the anti virus security guards, so you can use it on the garbage file (from Hackers), to reveal a clue to follow the "wht_rbt.obj" (Jurassic Park), which would eventually lead to a secret room that is the link to the March Hare. Somewhere in the middle you could have "write an iptables rule on a real Linux box to unlock a chest containing a reward item".

With the MUD puzzles, we want to lean hard towards puzzles that require teamwork to solve (e.g. need to explore a large state space and parallelization is the only efficient way). The EC2 instance puzzles will likely be fairly individualized and independent, because that is the nature of a traditional terminal.

Why is the MUD available before the boss fight? We recently discovered some leftover processes running in the Daemon from when the March Hare was around. We're pretty sure this was isolated from the March Hare last year, so go explore around and see what you can find. (Secret: it wasn't actually isolated)

# Development Setup
1. Install Docker
2. docker pull evennia/evennia
3. git clone git@github.com:thedarknet/evennia.git
4. cd /path/to/evennia && git checkout dn8 && docker run -it --rm -p 4000:4000 -p 4001:4001 -p 4002:4002 -p 4004:4004 -p 4005:4005 --rm -v $PWD:/usr/src/game evennia/evennia
5. evennia migrate && evennia start (loki, no email, stormbringer)
6. Open your browser to http://localhost:4001 or `ssh localhost -p 4004` or `telnet localhost 4000`
7. Login as loki with password stormbringer

# Diving into Evennia

This is your game directory, set up to let you start with
your new game right away. An overview of this directory is found here:
https://github.com/evennia/evennia/wiki/Directory-Overview#the-game-directory

From here on you might want to look at one of the beginner tutorials:
http://github.com/evennia/evennia/wiki/Tutorials.

Evennia's documentation is here:
https://github.com/evennia/evennia/wiki.

# DN8 Project Plan

## Grid Dungeon Framework
* Every room has a set of associated coordinates and exits in all valid cardinal directions (n,s,e,w)
* 2D grid of rooms with very selective up/down points that can be opened by external triggers
* External trigger system to allow an external event to change the state of an object (e.g. unlock a chest containing a reward item)
* Players "tunnel" to open exits into undiscovered rooms, at the cost of time and some kind of credits. Exits degrade over time and eventually collapse from disuse (maybe 5 minutes?).

## Accounts
* Easiest path is likely to have the Daemon create individual evennia accounts on demand (i.e. you complete a quest and that creates an account for you)
* evennia uses django auth underneath

## Acceptance Criteria
### Room Grid
In order to provide a predictable space for investigation
Given a build command file to generate the boss fight zone
When the command file is run
Then there should be a grid of identical rooms of the dungeon typeclass
And the rooms should be "weakly connected" in accordance with their location

Pretty simple: we need to generate the base layer of all the room objects with an understanding of which rooms are N,S,E,W of them so that players can then create tunnels between the rooms. This is going to require a common Typeclass for all the rooms that can later be inherited and modified (if necessary) for complex puzzle rooms.

### Obvious Boundaries
In order to curtail unnecessary "puzzle solving" when there is no puzzle to solve
Given a fixed sized dungeon grid
When a player attempts to tunnel beyond the grid
Then the player should get a clear message that this is not possible

### Player-created Tunnels
In order to create an air of mystery
And leave behind some breadcrumbs of "paths already explored"
Given a fixed sized dungeon grid
When a player tunnels in a new direction
Then the source and destination rooms should be linked in both directions

Counter case: don't allow tunneling if a tunnel already exists

### Build Command File Conventions
In order to efficiently coordinate worldbuilding across multiple teams
And enable easy recreation of the game database for playtesting
Then we need a convention for organizing puzzles in the build command file

This is less technical implementation and more forethought and planning. We need to figure out how we want the puzzle builders to organize their puzzles to avoid ending up with a spaghetti mess that is impossible to debug in the hectic moments during DEFCON.

### Easter Egg Rooms (up/down)
### Decaying Tunnels
### Costly Tunnels
### Solve Puzzles To Earn Credits (SPTEC)


### Daemon-triggered account creation
In order to enforce teamwork
And prevent a single player from puppeting multiple characters
Given every player has a single Agent account in the Daemon
When the player tries to access the MUD from the Daemon
Then the Daemon should create a matching user account in the MUD
And the MUD account should have a reference to the matching DarkNet Agent account (could be just by name)

I imagine this looks something like a "Set up your account" Quest that uses a Remote Objective to trigger the create account/character process in Evennia. This will be one of two external event use cases in evennia, so the actual event processing part is a separate task.

### External Event Processing System
In order to create a more immersive game that is connected to "the outside world"
Given a standalone puzzle outside the MUD
When the puzzle is solved
Then an event should be emitted that abstractly describes a MUD state transition
And Evennia should consume that event
And Evennia should execute the described state transition

I'm imagining a queue of external events (puzzle completions, account creations, more?) and an Evennia Script (which is Evennia's concept of a long-running process) that pops events off the queue and processes that event similar to an RPC (i.e. event has a method to call or a property to update). I wonder if this means some kind of mapping file on the Evennia side of "event name -> function to call w/ args". Purpose: try to keep the external puzzle separate from the Evennia implementation and independent of any later Evennia changes, so probably a unique event for each puzzle, even if that maps to the same function over and over.


## Puzzle Building
* Describe the overall puzzle flows and how they interact together (including EC2 puzzles!)
* Build out a spreadsheet describing the "map" and what belongs where
* Describe in detail how each puzzle/room should behave (including EC2 puzzle interactions)
* Implement everything one room/puzzle at a time as typeclasses (Python) and objects (evennia build commands)

# Example Puzzle: Accounting Worm
Goal: recreate the accounting worm from Hackers that is nibbling off pennies from each transaction

## Describe the overall puzzle flow
* NPC generator: financial transactions moving through multiple rooms to deposit in the correct "table"/"audit log"
* NPC: worm moving randomly between rooms and "nibbling" cents off of transactions
* Object: each room has a "table" listing all the transaction NPCs that have been recorded in it
* Possible solutions: catch the worm, kill the worm, trap the worm, bring in a bird to eat the worm
* Bird/Worm could have all the stolen money inside it

## Describe how the puzzles should behave
```
transaction 19237 appears in accounting room 3
> look transaction 19237
Transaction 19237
AP $1827.18

transaction 19237 records in the audit log
worm enters accounting room 3 from accounting room 4
transaction 19238 appears in accounting room 3
> look transaction 19238
Transaction 19238
AR $193.46

worm nibbles a little bit off of transaction 19238
> look transaction 19238
Transaction 19238
AR $193.19

transaction 19238 records in the audit log
> drop bird
bird eats worm
> look bird
Bird
A bird with $102,938.73 inside it
bird drops money and flies away
> take money
You're rich!
```

## Convert into evennia concepts
* Script: TransactionGenerator (generates transactions)
  * New transaction with random amount generated in a random accounting room every 30 seconds
* Object: Transaction
  * Dumb object that can be looked at to see the value and payable/receivable
  * Transactions "commit" into the local audit log after 30 seconds (ticker)
  * Can't be picked up or otherwise manipulated
* Object: Worm (Mobile NPC)
  * Moves to a random accounting room every 15 seconds
  * If a transaction arrives while the worm is in the room, the worm will nibble the transaction (modifying it)
  * If a player attempts to grab it, the worm immediately moves to a new accounting room
* Object: Audit Log (ring buffer with the last 10 transactions)
  * Dumb object with a ring buffer of the last 10 transaction committed in this room
  * Look: show the ring buffer of transactions: number+AR/AP+amount
  * Can't be picked up or otherwise manipulated
* Object: Bird (eats the Worm)
  * If the bird is in a room and the worm is in the same room, the bird immediately eats the worm
  * Monitor for "dropped in a room", "used on another object" (maybe?), and "another object entered the room"
  * States
    * Initial
      * on look, "a small bird. It looks hungry."
      * on eatworm, goto Eaten a worm
    * Eaten a worm (full of money)
      * on look, drop a money object and fly away (destroy object)
* Object: Money (maybe?)
  * Fixed amount
