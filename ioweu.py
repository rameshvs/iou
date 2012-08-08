from __future__ import division
from __future__ import print_function

import sys
import numpy as np

# version 0.1: no input error checking, no graph simplification
class DebtTracker(object):

    def __init__(self, names):
        # who 
        self.names = [name.lower() for name in names]
        self.N = len(names)
        # since we use spaces to tokenize input, we can't have spaces in
        # names. we also can't have any of the reserved keywords used as names
        for name in self.names:
            assert ' ' not in name
            assert name not in ['help','print','add','debug']

        # a skew-symmetric matrix tracking debts: if debt_graph[i,j] = a, then i
        # owes j $a, and debt_graph[j,i] = -a.
        self.debt_graph = np.zeros([self.N,self.N])

    def add_debts(self, debtors, lender, amount):
        # each debtor in debtor owes exactly amount to lender
        added_edges = np.zeros([self.N,self.N])
        lender = self._lookup(lender)
        for debtor in map(self._lookup,debtors):
            added_edges[debtor,lender] = amount
            added_edges[lender,debtor] = -amount
        self.debt_graph += added_edges

    def print_help(self):
        usage_string = """\
        Accepted expressions:
            'help'
            'print'
            'debt <name> owes <name> <amount>'
            'debt <name> paid <amount> for <names separated by spaces>'
            'add <new users separated by spaces>'"""
        print(usage_string)

    def _lookup(self, name):
        """ Returns the index of a particular name. For internal use only """
        return self.names.index(name)

    def parse_command(self, command):
        tokens = command.lower().split(' ')
        if tokens[0] == 'print':
            self.print_debts()
        elif tokens[0] == 'help':
            self.print_help()
        elif tokens[0] == 'debug':
            print(repr(self.debt_graph))
        elif tokens[0] == 'debt' and tokens[2] == 'owes':
            (debtor,_,lender,amount_string) = tokens[1:]
            self.add_debts([debtor],lender,float(amount_string))
        elif tokens[0] == 'debt' and tokens[2] == 'paid':
            (lender,_,total_amount_string) = tokens[1:4]
            debtors = tokens[5:]
            amount = float(total_amount_string) / len(debtors)
            self.add_debts(debtors,lender,amount)
        elif tokens[0] == 'add':
            self.names.extend(tokens[1:])
            new_N = self.N + len(tokens[1:])

            new_debt_graph = np.zeros([new_N,new_N])
            new_debt_graph[:self.N,:self.N] = self.debt_graph

            self.debt_graph = new_debt_graph
            self.N = new_N
        else:
            print("** Unknown/unparseable command, please try again: %s"%command)

    def print_debts(self):
        for i in xrange(self.N):
            for j in xrange(i):
                amount = self.debt_graph[i,j]
                if amount == 0:
                    continue
                elif amount < 0:
                    (debtor,lender) = (j,i)
                elif amount > 0:
                    (debtor,lender) = (i,j)
                else:
                    raise ValueError("serious error: numbers should always be =, >, or < 0")
                print("%s owes %s $%0.2f"%(self.names[debtor],self.names[lender],abs(amount)))

    def simplify_debts(self):
        # tries to sparsify debt matrix. for example, if A owes B $1 and B owes
        # C $1, then this can be simplified to "A owes C $1".
        pass

def main(names):
    dt = DebtTracker(names)
    while True:
        cmd = raw_input("> ")
        dt.parse_command(cmd)

if __name__ == '__main__':
    main(sys.argv[1:])
