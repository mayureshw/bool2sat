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

NOTE: The command line usage is deprecated. May be restored in future.

python3 bool2sat.py [formula filename]

You can write your formula in a file and provide filename as an argument.

Alternatively you can drop the filename and either pipe or type in the formula on stdin.

If there are parsing errors, it would just give a curt 'parse error' message. Sorry, no detailed message, we don't get one form the parser package.

Else it would produce a DIMACS formula in file cnf.txt, run minisat on it and show the output on stdout. Besides it will produce satop.txt in which minisat would generate feasible solution, if found. The feasible solution would be translated back to user's variables and printed.


## As API

import the CNF class from bool2sat.

### Constructing a CNF object

You can construct a cnf object by one of the following methods:

All construction methods mandate naming the formula with a variable. It is caller's responsibility to keep the naming unique, otherwise the results can be unpredictable.

1. byformula: Pass a boolean formula. See a link to the formula grammar below.
2. byequation: You can pass multiple formulas in a dictionary with their variable names as the key. This is the most common and useful construction method to represent complex circuits.
3. bymerge: You can take multiple cnf formulas already constructed and merge them (logically and) into one by passing to this method.
4. let: Substitute a given variable with a given truth value and return new cnf object. Note that, for consistency with other formulas, all variables other than input variables are transformed to new values.

Note that 'by*' are class APIs, to be usually invoked as CNF.<api> while 'let' is to be invoked on an existing object on which it will carry out substitution

### Important APIs on the CNF object

1. minisat: Runs minisat on the CNF and returns a solution in terms of user varaibles if found, else returns false.

2. bdd: Returns a bdd representation of a CNF. Returns a tuple of bdd of the formulas as-is and with intermediate variables existentially quantified. This is not the core functionality, since you would use SAT on problems where bdds won't usually scale! But it can be useful during development, for example, to see a compact representation of the formula etc. At present a module required to use this functionality is not included in the package. May add it in future.


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
