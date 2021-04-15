# We reuse the parser from the dd package, but we do not use bdds
from dd._parser import Parser
from functools import reduce
import subprocess
import sys
from pybdd import BMgr # Only for development purposes
class CNF:
    bmgr = BMgr()

    # Various CNF transformations are taken from here:
    # https://en.wikipedia.org/wiki/Tseytin_transformation There is virtually
    # no restriction on adding operators. Any single output operator can be
    # added with just 1 line entry in the table.
    #
    # Convention to write this table:
    # Each operator's transformation is a list of lists. Outer list is of
    # conjunctions, inner of disjunctions. Integers in the inner list indicate:
    # 1: output node, 2,3... positional argument nodes.
    # '-' sign: indicates negation
    cnftbl = {
        '&' : [[-2,-3,1],[2,-1],[3,-1]],
        '!' : [[1,2],[-1,-2]],
        '|' : [[-1,2,3],[1,-2],[1,-3]],
        '^' : [[-1,-2,-3],[-1,2,3],[1,2,-3],[1,-2,3]],
        }
    cnfopfile = 'cnf.txt'
    satopfile = 'satop.txt'
    parser = Parser()
    nodecntr = 0
    _varid = {}
    def varid(self,v):
        if v in CNF._varid: return CNF._varid[v]
        newid = self.nextid()
        CNF._varid[v] = newid
        return newid
    def nextid(self):
        CNF.nodecntr = CNF.nodecntr + 1
        return CNF.nodecntr
    def spec2cnf(self,spec,args): return [ (-1 if i<0 else 1)*args[abs(i)-1] for i in spec ]
    def _cnf(self,node): return (
        [self.spec2cnf(sumspec, [node.id]+[o.id for o in node.operands])
            for sumspec in self.cnftbl[node.operator]] +
        [cnf for c in node.operands if c.type=='operator' for cnf in self._cnf(c)]
        ) if node.type == 'operator' else [[node.id]]
    # opvar ANDing is added on the fly to allow easy merging of formulas
    def cnf(self,opvarid=None): return self.cnfworoot + [[opvarid if opvarid else self.opvarid]]
    def visit(self,node,idgiven=False):
        if node.type == 'operator':
            if not idgiven: node.id = self.nextid()
            for arg in node.operands: self.visit(arg)
        else:
            node.id = self.varid(node.value)
            self.inpvars.add(node.id)
    def dimacs(self,opvarid=None): return ' '.join(' '.join(
        str(d) for d in c+[0]) for c in self.cnf(opvarid))

    # Generate cnf in dimacs form in cnfopfile
    def dump(self,opvarid=None):
        with open(self.cnfopfile,'w') as fd: fd.write(self.dimacs(opvarid))

    # Run minisat and report results and if satisfiable decode the solution into user's variables
    # eliminating intermediate variables
    def minisat(self,opvarid=None):
        self.dump(opvarid)
        satop = subprocess.run(['minisat',self.cnfopfile,self.satopfile],
            capture_output=True, encoding='ascii')
        if satop.returncode == 10:
            idvar = { i:v for v,i in self._varid.items() if i in self.inpvars }
            with open(self.satopfile) as fd:
                satsoln = [int(i) for i in fd.readlines()[-1].split()[:-1]]
            return ', '.join([(idvar[abs(i)] + '=' + ('0' if i<0 else '1'))
                for i in satsoln if abs(i) in idvar])
        else: return 'false'

    # returns a transformed object by replacing output with opvar and
    # substituting 0/1 as per v,tv . Uses new values for intermediate nodes.
    def xform(self,opvar,v,tv):
        o = CNF(opvar)
        vid = self.varid(v)
        # apply truth value v=tv
        elimsumwith = vid if tv else -vid
        elimvar = -vid if tv else vid
        o.cnfworoot = [ [e for e in sumterm if e!= elimvar ]
            for sumterm in self.cnfworoot if elimsumwith not in sumterm ]
        intervars = { abs(v) for sumterm in o.cnfworoot for v in sumterm if abs(v) not in self.inpvars }
        subst = { v:self.nextid() for v in intervars }
        subst[self.opvarid] = o.opvarid
        substf = lambda l: [(subst.get(v,v) if v>0 else -subst.get(-v,-v) ) for v in l]
        o.cnfworoot = [ substf(sumterm) for sumterm in o.cnfworoot ]
        o.definedvars = set(substf(d for d in self.definedvars if d!= vid) + [o.opvarid])
        o.inpvars = substf(i for i in self.inpvars if i!= vid)
        return o

    # bdd is only for experimental purpose, returns a tuple of bdd and with op
    # and intermediate variables quatified out
    def bdd(self):
        cnf = self.cnfworoot
        idvar = { i:v for v,i in self._varid.items() }
        n2v = lambda n: idvar.get(abs(n),'v'+str(abs(n)))
        self.bmgr.declare(*[ n2v(t) for p in cnf for t in p ])
        n2bv = lambda n: ('~' if n<0 else '')+n2v(n)
        bdd = self.bmgr.andL(self.bmgr.orL(self.bmgr.add_expr(n2bv(t)) for t in p) for p in cnf)
        bddo = self.bmgr.shcf1(bdd,self.opvar)
        qvars = [s for s in self.bmgr.support(bdd) if s not in self._varid]
        bddv = self.bmgr.equantL(bddo,qvars)
        return bdd,bddv

    # We follow factory pattern of construction, to make it easy to construct blank objects
    # which is required in operator overloading for and

    # Construction method by naming an opvar and a formula (string)
    @classmethod
    def byformula(cls,opvar,formula):
        o = CNF(opvar)
        try: root = o.parser.parse(formula)
        except Exception:
            print('parse error in',formula)
            sys.exit()
        # for atomic formula we need special handling, for now, and with itself
        if root.type != 'operator': root = o.parser.parse(formula + '&' + formula)
        root.id = o.opvarid
        o.inpvars = set()
        o.visit(root,idgiven=True)
        o.cnfworoot = o._cnf(root)
        o.definedvars = {o.opvarid}
        o.inpvars = o.inpvars - o.definedvars
        return o

    # Method to construct cnf from a number of variables in a dictionary eqns and top opvar
    @classmethod
    def byequations(cls,opvar,eqns): return CNF.bymerge(opvar,
        [CNF.byformula(o,f) for o,f in eqns.items()])

    def mergein(self,other):
        self.cnfworoot = self.cnfworoot + other.cnfworoot
        self.definedvars.update(other.definedvars)
        self.inpvars = self.inpvars.union(other.inpvars) - self.definedvars
        return self
    # Method to construct cnf by merger of multiple cnfs
    @classmethod
    def bymerge(cls,opvar,cnfs): return reduce(lambda c1,c2: c1.mergein(c2), cnfs, CNF(opvar))

    # Constructor not meant to be invoked from outside, please use by* methods above
    def __init__(self,opvar=None):
        self.opvar = opvar
        self.opvarid = self.varid(opvar)
        self.cnfworoot = []
        self.definedvars = set()
        self.inpvars = set()

# When opvar support was added CLI was removed. A new CLI may be added later
# This is merely a test driver now
if __name__=='__main__':
    cnf1 = CNF.byformula('p','a&b')
    print(cnf1.minisat())

    cnf2 = CNF.byformula('q','p&d')
    print(cnf2.minisat())

    cnf3 = CNF.bymerge('q',[cnf1,cnf2])
    print(cnf3.minisat())

    cnf4 = CNF.byequations('q',{'p':'a&b','q':'p&d',})
    print(cnf4.minisat(-cnf2.varid('p')))
