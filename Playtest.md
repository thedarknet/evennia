# Test extra rooms
```
# visit grue room (4,7) and get eaten/sent back to Entrance (1,7) when you leave
(9,7) look smile
(0,3) look painting
look safe
get crowbar
(1,10) use crowbar on crate
get flashlight
# visit grue room (4,7) and don't die when you leave
```
```
get keyboard
use keyboard on screen
```
# Test funhouse
From the Entrance room: n,n,n to get into the room; now every time you go any direction but south, you should just see the room color change. If you go s,s,s (no matter what you did inside the room), you should be back in the Entrance room.
# Retrieve the cryptochip and get caught
From the Entrance room:
w,n,n,n,n, n,n,e
`say my voice is my passport`
`get cryptochip`
wait patiently for the antibodies to find you and throw you in jail
You should be automatically released from jail and sent back to the Entrance room
# Disable antibodies
You'll need a partner for this.
Person 1: head to playtronics and wait
Person 2: head to the AntiVirus room; e,e,e,n,n
Person 1: pick up the cryptochip, go `ne`, `drop cryptochip` (so you don't get thrown in jail)
Person 2: `look antivirus control console` ; navigate to "Configuration" and disable the smart and horizontal antibodies
# Install cryptochip
You'll need a partner for this
Person 1: head to playtronics and wait
Person 2: head to antivirus room
Person 1: pick up the crypto chip
Person 2: `get antibody` as soon as it appears in the room
Person 1: head to the CPU room: e,s,s,s,s, e,e
Person 1: `drop cryptochip`, `look cpu` and see that there is now a cryptochip installed
# Update firewall (WIP)
# Decrypt garbage file
Go to god's room (6,9)
`get garbage`
Go to CPU room (4,5)
`drop garbage`
`decrypt garbage`
# Test accounting trap
This requires 10 people or modifying the code to require fewer people to release the lock
# Stop accounting worm
Go to (3,8) and `get bird`
Go to accounting (9,1) avoiding the accounting trap rooms
Wait for the worm to arrive in the room and `drop bird`
`look bird`
`get money`
`look money` and see that you have some quantity of money
# Disconnect March Hare (WIP)
Go to the secret exit (9,2) and `fini.obj`
See that you get put into the meet-me room
`disconnect daemon`
See that there is a public announcement about the daemon being disconnected
`disconnect march hare`
See that there is a public announcement about the march hare being disconnected
See that you are moved to Limbo and the zone:cyberez exit is no longer there