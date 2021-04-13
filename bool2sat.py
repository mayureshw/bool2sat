# We reuse the parser from the dd package, but we do not use bdds
from dd._parser import Parser
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
    varid = {}
    def nextid(self):
        CNF.nodecntr = CNF.nodecntr + 1
        return CNF.nodecntr
    def spec2cnf(self,spec,args): return [ (-1 if i<0 else 1)*args[abs(i)-1] for i in spec ]
    def _cnf(self,node): return (
        [self.spec2cnf(sumspec, [node.id]+[o.id for o in node.operands])
            for sumspec in self.cnftbl[node.operator]] +
        [cnf for c in node.operands if c.type=='operator' for cnf in self._cnf(c)]
        ) if node.type == 'operator' else [[node.id]]
    def visit(self,node):
        if node.type == 'operator':
            node.id = self.nextid()
            for arg in node.operands: self.visit(arg)
        else:
            if node.value in CNF.varid:
                node.id = CNF.varid[node.value]
            else:
                node.id = self.nextid()
                CNF.varid[node.value] = node.id
    def dimacs(self): return ' '.join(' '.join(str(d) for d in c+[0]) for c in self.cnf)

    # Generate cnf indimacs form in cnfopfile
    def dump(self):
        with open(self.cnfopfile,'w') as fd: fd.write(self.dimacs())

    # Run minisat and report results and if satisfiable decode the solution into user's variables
    # eliminating intermediate variables
    def minisat(self):
        satop = subprocess.run(['minisat',self.cnfopfile,self.satopfile],
            capture_output=True, encoding='ascii')
        print(satop.stdout)
        if satop.returncode == 10:
            print('Decoding the satisfiable assigment...')
            idvar = { i:v for v,i in CNF.varid.items() }
            with open(self.satopfile) as fd:
                satsoln = [int(i) for i in fd.readlines()[-1].split()[:-1]]
            usersoln = [('~' if i<0 else '') + idvar[abs(i)] for i in satsoln if abs(i) in idvar]
            print(' '.join(usersoln))
            
    def __init__(self,formula):
        try: root = self.parser.parse(formula)
        except Exception:
            print('parse error')
            sys.exit()
        self.visit(root)
        self.cnf = self._cnf(root) + [[1]]
    
# If invoked as command, reads boolean formula from filename if specified as
# argument else from stdin. Produces cnf.txt and satop.txt and minisat stdout
if __name__=='__main__':
    fd = sys.stdin if len(sys.argv)<2 else open(sys.argv[1])
    cnf = CNF(fd.read())
    cnf.dump()
    cnf.minisat()
