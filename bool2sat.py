# We reuse the parser from the dd package, but we do not use bdds
from dd._parser import Parser
from functools import reduce
import subprocess
import sys
class CNF:
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
        else: node.id = self.varid(node.value)
    def dimacs(self,opvarid=None): return ' '.join(' '.join(
        str(d) for d in c+[0]) for c in self.cnf(opvarid))

    # Generate cnf indimacs form in cnfopfile
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
            
    # setting of opvarid and trimming of inpvars has to be handled by caller,
    # treat & operator for internal use unless you know what you are doing
    def __and__(self,rval):
        o = CNF()
        o.cnfworoot = self.cnfworoot + rval.cnfworoot
        o.inpvars = self.inpvars.union(rval.inpvars)
        return o

    # We follow factory pattern of construction, to make it easy to construct blank objects
    # which is required in operator overloading for and

    # Construction method by naming an opvar and a formula (string)
    @classmethod
    def byformula(cls,opvar,formula):
        o = CNF()
        try: root = o.parser.parse(formula)
        except Exception:
            print('parse error')
            sys.exit()
        o.opvarid = o.varid(opvar)
        root.id = o.opvarid
        o.visit(root,idgiven=True)
        o.cnfworoot = o._cnf(root)
        o.inpvars = { v for p in o.cnfworoot for v in p if v != o.opvarid }
        return o

    # Method to construct cnf from a number of variables in a dictionary eqns and top opvar
    @classmethod
    def byequations(cls,opvar,eqns):
        o = reduce(lambda l,r: l&r, [CNF.byformula(o,f) for o,f in eqns.items()])
        o.opvarid = o.varid(opvar)
        o.inpvars = o.inpvars - { o.varid(v) for v in eqns }
        return o
    
# When opvar support was added CLI was removed. A new CLI may be added later
# This is merely a test driver now
if __name__=='__main__':
    cnf1 = CNF.byformula('p','a&b')
    print(cnf1.minisat())

    cnf2 = CNF.byequations('q',{'p':'a&b','q':'p&d',})
    print(cnf2.minisat(-cnf2.varid('p')))
