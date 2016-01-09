class Target(object):
    def getDevice(self):
        raise NotImplementedError(type(self).__name__ + ".getDevice")

    def __enter__(self):
        self.getDevice().pushTarget(self)

    def __exit__(self, type, value, traceback):
        self.getDevice().popTarget()

    def setVar(self, fsm, state):
        raise NotImplementedError(type(self).__name__ + ".setVar")

class Assignments(object):
    __slots__ = "assignments vars".split()

    def __init__(self):
        self.assignments = []
        self.vars = set()

    def setVar(self, var, state):
        assert var not in self.vars, var
        self.assignments.append((var, state))
        self.vars.add(var)

    def dump(self, indent):
        print "%sassign {" % indent
        for var, val in self.assignments:
            print "%s\t%s << %s" % (indent, var.name, val.name) # HACK
        print "%s}" %indent

class Device(object):
    __slots__ = "name exists types vars msgs cache target stack".split()

    def __init__(self, name):
        self.name = name
        self.exists = set([name])
        self.types = []
        self.vars = []
        self.msgs = []
        self.cache = PredicateCache()
        self.target = None
        self.stack = []

    def fsm(self, name):
        assert name not in self.exists, name
        self.exists.add(name)
        fsm = FiniteStateMachine(self, name)
        self.types.append(fsm)
        return fsm

    def var(self, name, type, initial):
        assert name not in self.exists, name
        type.assertValueIsOK(initial)
        self.exists.add(name)
        var = Var(self, len(self.vars), name, type, initial)
        self.vars.append(var)
        return var

    def msg(self, name):
        assert name not in self.exists, name
        self.exists.add(name)
        msg = Message(self, name)
        self.msgs.append(msg)
        return msg

    def canonicalName(self):
        return self.name

    def pushTarget(self, target):
        self.stack.append(self.target)
        self.target = target

    def popTarget(self):
        self.target = self.stack.pop()

    def getDevice(self):
        return self

    def dump(self):
        print "device %s {" % self.name
        print "types:"
        for t in self.types:
            t.dump()
        print "vars:"
        for v in self.vars:
            v.dump()
        print "msgs:"
        for m in self.msgs:
            m.dump()
        print "}"

class FiniteStateMachine(object):
    __slots__ = "device name stateList stateLUT".split()

    def __init__(self, device, name):
        self.device = device
        self.name = name
        self.stateList = []
        self.stateLUT = {}

    def state(self, name):
        assert name not in self.stateLUT, name
        s = State(self, name)
        self.stateList.append(s)
        self.stateLUT[name] = s
        return s

    def states(self, names):
        return [self.state(name) for name in names.split()]

    def assertValueIsOK(self, value):
        if value.fsm is not self:
            raise Error(value)

    def canonicalName(self):
        return self.device.canonicalName() + "." + self.name

    def getDevice(self):
        return self.device

    def dump(self):
        print "\tfsm %s {" % self.name
        for s in self.stateList:
            s.dump()
        print "\t}"

class State(object):
    __slots__ = "fsm name".split()

    def __init__(self, fsm, name):
        self.fsm = fsm
        self.name = name

    def canonicalName(self):
        return self.fsm.canonicalName() + "." + self.name

    def dump(self):
        print "\t\tstate %s" % self.name

    def __eq__(self, value):
        raise NotImplementedError(self.name)

    def __ne__(self, value):
        raise NotImplementedError(self.name)

class Var(object):
    __slots__ = "device index name type initial".split()

    def __init__(self, device, index, name, type, initial):
        self.device = device
        self.index = index
        self.name = name
        self.type = type
        self.initial = initial

    def canonicalName(self):
        return self.device.canonicalName() + "." + self.name

    def getDevice(self):
        return self.device

    def __lshift__(self, other):
        assert other.fsm is self.type, other
        self.getDevice().target.setVar(self, other)

    def dump(self):
        print "\tvar %s %s = %s" % (self.name, self.type.canonicalName(), self.initial.canonicalName())

    def __eq__(self, value):
        self.type.assertValueIsOK(value)
        f = self.device.cache.const(False)
        t = self.device.cache.const(True)
        children = [t if state is value else f for state in self.type.stateList]
        return self.device.cache.fsm(self, children)

    def __ne__(self, value):
        self.type.assertValueIsOK(value)
        f = self.device.cache.const(False)
        t = self.device.cache.const(True)
        children = [t if state is not value else f for state in self.type.stateList]
        return self.device.cache.fsm(self, children)

class PredicateCache(object):
    def __init__(self):
        self.false = ConstPredicate(self, False)
        self.true = ConstPredicate(self, True)

    def const(self, value):
        return self.true if value else self.false

    def fsm(self, var, children):
        return FSMPredicate(var, children)

class ConstPredicate(object):
    __slots__ = "cache value".split()
    def __init__(self, cache, value):
        self.cache = cache
        self.value = value

    def __eq__(self, other):
        if self is other:
            return True
        return type(self) is type(other) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __and__(self, other):
        return other if self.value else self

    def __or__(self, other):
        return self if self.value else other

    def exprString(self):
        return repr(self.value)

class FSMPredicate(object):
    __slots__ = "var children".split()
    def __init__(self, var, children):
        self.var = var
        self.children = children

    def exprString(self):
        return "%s => (%s)" % (self.var.canonicalName(), ", ".join([child.exprString() for child in self.children]))

    def __eq__(self, other):
        if self is other:
            return True
        if type(self) is type(other) and self.var is other.var:
            for a, b in zip(self.children, other.children):
                if not a == b:
                    return False
                return True
        return False

class Message(Target):
    __slots__ = "device name pre assign".split()

    def __init__(self, device, name):
        self.device = device
        self.name = name
        self.pre = None
        self.assign = Assignments()

    def precondition(self, pred):
        self.pre = pred

    def getDevice(self):
        return self.device

    def setVar(self, var, state):
        self.assign.setVar(var, state)

    def dump(self):
        print "\tmessage %s {" % self.name
        if self.pre is not None:
            print "\t\tprecondition: " + self.pre.exprString()
        self.assign.dump("\t\t")
        print "\t}"
