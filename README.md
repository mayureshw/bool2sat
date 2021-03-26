# bool2sat
Convert arbitrary boolean formula to CNF and Run SAT solver on it

SAT solvers require a boolean formula to be in the CNF form. This program converts an arbitrary boolean formula into DIMACS CNF form, runs minisat SAT solver on it and translates the satisfiability result (if any) back into user variables.

# System requirements

- Python3

- Python dd package

Most typical way to install: pip3 install dd

While dd is a bdd package, we merely use the boolean formula parser from it. We do not use the bdd functionality.

- minisat SAT solver

Most typical way to install: apt install minisat

# Usage

## Command line

python3 bool2sat.py [formula filename]

You can write your fomula in a file and provide filename as an argument.

Alternatively you can drop the filename and either pipe or type in the formula on stdin.

If there are parsing errors, it would just give a curt 'parse error' message. Sorry, no detailed message, we don't get one form the parser package.

Else it would produce a DIMACS formula in file cnf.txt, run minisat on it and show the output on stdout. Besides it will produce satop.txt in which minisat would generate feasible solution, if found. The feasible solution would be translated back to user's variables and printed.


## As API

import the CNF class from bool2sat, construct a cnf object by passing the formula string to it. Look at the dump and minisat APIs that do the things described above.

# Boolean formula grammar

For formal grammar of the formula please refer to the parser documentation at the following link:

https://github.com/tulip-control/dd/blob/master/doc.md

# How to add support for more operators

Adding support for more operators is easy, requiring just a one line entry in cnftbl. The format of this table is documented in the program. Do consider submitting a patch if you add operators.

# BUGS

All ears...

# Wishlist

- Support for more operators. Currently only &,|,~ and ^ are supported.

- Support for more SAT solvers. Currently only minisat is supported.

- Replace recursive logic in CNF conversion with iterative. If someone wants to use this on really large formulas, python recursion depth would come in play. Of course, one may increase the stack size as a quick solution.

- Use a standalone parser package instead of installing dd just for the parser.
