#!/usr/bin/python

import arbiter

mutex = arbiter.Device("mutex")
b = mutex.fsm("bool")
f, t = b.states("false true")
is_locked = mutex.var("is_locked", b, f)

lock = mutex.msg("lock")
with lock:
    is_locked << t

unlock = mutex.msg("unlock")
unlock.precondition(is_locked == t)
with unlock:
    is_locked << f

mutex.dump()
