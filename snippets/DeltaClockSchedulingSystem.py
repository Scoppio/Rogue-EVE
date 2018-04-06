"""Extras
Another problem that can solved using the delta clock is act order. Supposing you put both the player and monsters into the delta clock
 structure, and that you have a generic actor interface for both player and monster, you may have a problem if on one tick the player
 happens to come early in the queue, and later on another tick. To the player, this will apparently allow the monster to occasionally
 take extra turns, and occasionally allow the player to take extra turns, which can be disorienting.
A simple solution to this is to schedule the player at a fractional offset. If you schedule the player initially at .5 ticks,
and monsters at 1 tick, and then have every actor be scheduled in whole tick increments, the player will always be in an event without
 any monsters, meaning that no one will ever apparently lose a turn."""


class DeltaClock(object):
    class Node(object):
        def __init__(self, delta, link):
            self.delta = delta
            self.link = link
            self.events = set()

    def __init__(self):
        self.head = None
        self.nodes = {}

    def schedule(self, event, delta):
        assert event not in self.nodes

        prev, curr = None, self.head
        while curr is not None and delta > curr.delta:
            delta -= curr.delta
            prev, curr = curr, curr.link

        if curr is not None and delta == curr.delta:
            node = curr
        else:
            node = DeltaClock.Node(delta, curr)
            if prev is None:
                self.head = node
            else:
                prev.link = node
            if curr is not None:
                curr.delta -= delta

        node.events.add(event)
        self.nodes[event] = node

    def advance(self):
        events = self.head.events
        for event in events:
            del self.nodes[event]
        self.head = self.head.link
        return events

    def unschedule(self, event):
        self.nodes[event].events.remove(event)
        del self.nodes[event]
