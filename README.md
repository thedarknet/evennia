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
8. batchcode bossfightzone   (this will take a few minutes with no output to execute)

# Diving into Evennia

This is your game directory, set up to let you start with
your new game right away. An overview of this directory is found here:
https://github.com/evennia/evennia/wiki/Directory-Overview#the-game-directory

From here on you might want to look at one of the beginner tutorials:
http://github.com/evennia/evennia/wiki/Tutorials.

Evennia's documentation is here:
https://github.com/evennia/evennia/wiki.

# DN8 Projects
1. [Boss Fight Framework](https://github.com/thedarknet/evennia/projects/1)
2. [Example Puzzle: Accounting Worm](https://github.com/thedarknet/evennia/projects/3)
3. [Boss Fight Puzzles](https://github.com/thedarknet/evennia/projects/4)
