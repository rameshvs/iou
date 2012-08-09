from __future__ import division
from __future__ import print_function

import math
import sys
import numpy as np

from IPython.core.debugger import Tracer
debug_here = Tracer()

# version 0.2: graph simplification works, minimal input checking/error handling
class DebtTracker(object):

    def __init__(self, names):

        self.names = [name.lower() for name in names]
        self.N = len(names)
        # since we use spaces to tokenize input, we can't have spaces in
        # names. we also can't have any of the reserved keywords used as names
        for name in self.names:
            assert ' ' not in name
            assert name not in ['help','print','add','debug','d','debt','all','simplify']

        # a skew-symmetric matrix tracking debts: if debt_graph[i,j] = a, then i
        # owes j $a, and debt_graph[j,i] = -a.
        self.debt_graph = np.zeros([self.N,self.N])

    def add_debts(self, debtors, lender, amount):
        # each debtor in debtor owes exactly amount to lender
        added_edges = np.zeros([self.N,self.N])
        for debtor in debtors:
            added_edges[debtor,lender] = amount
            added_edges[lender,debtor] = -amount
        self.debt_graph += added_edges

    def print_help(self):
        usage_string = """\
        Accepted expressions:
            'help'
            'print'
            'simplify'
            'd[ebt] <name> owes <name> <amount>'
            'd[ebt] <name> paid <amount> for <names separated by spaces>'
            'd[ebt] <name> paid <amount> for all'
            'add <new users separated by spaces>'"""
        print(usage_string)

    def _lookup(self, name):
        """ Returns the index of a particular name. For internal use only """
        return self.names.index(name)

    def parse_command(self, command):
        handler = {
                'print': lambda tokens: self.print_debts(),
                'help': lambda tokens: self.print_help(),
                'debug': lambda tokens: debug_here(),
                'simplify': lambda tokens: self.simplify_debts(),
                'd': self.handle_debt_command,
                'debt': self.handle_debt_command,
                'add': self.handle_add_command,
                'clear': lambda tokens: self.handle_clear_command()
                }
        tokens = command.strip().lower().split(' ')
        if tokens[0] in handler:
            handler[tokens[0]](tokens)
        else:
            print("** Unknown/unparseable command, please try again")

    def handle_debt_command(self, tokens):
        if tokens[2] == 'owes':
            (debtor,_,lender,amount_string) = tokens[1:]
            self.add_debts([self._lookup(debtor)], self._lookup(lender), float(amount_string))
        elif tokens[2] == 'paid':
            (lender,_,total_amount_string) = tokens[1:4]
            debtors_raw = tokens[5:]
            if debtors_raw == ['all']:
                debtors = range(self.N)
                debtors.remove(self._lookup(lender))
            else:
                debtors = map(self._lookup, debtors_raw)
            amount = float(total_amount_string) / (len(debtors) + 1)
            self.add_debts(debtors, self._lookup(lender), amount)
        else:
            print("** Debt commands must contain 'owes' or 'paid'")

    def handle_add_command(self, tokens):
        self.names.extend(tokens[1:])
        new_N = self.N + len(tokens[1:])

        new_debt_graph = np.zeros([new_N,new_N])
        new_debt_graph[:self.N,:self.N] = self.debt_graph

        self.debt_graph = new_debt_graph
        self.N = new_N

    def handle_clear_command(self):
        self.debt_graph = np.zeros([self.N,self.N])

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
        # TODO think about convergence, and how many iterations need to be done
        for i in xrange(self.N):
            row = self.debt_graph[i,:]
            sign = np.sum(row)
            if sign >= 0:
                to_remove = np.flatnonzero(row < 0)
                to_keep = np.flatnonzero(row > 0)
            elif sign < 0:
                to_remove = np.flatnonzero(row > 0)
                to_keep = np.flatnonzero(row < 0)

            to_process = [to_remove,to_keep]

            while len(to_process[0]) > 0:
                (remove_index, keep_index) = zip(*to_process)[0]
                (removing,keeping) = (row[remove_index], row[keep_index])
                if abs(removing) < abs(keeping):
                    amount = removing
                    list_to_shorten = 0
                else:
                    amount = keeping
                    list_to_shorten = 1

                signed_amount = math.copysign(amount,keeping)

                self.add_debts([i], remove_index, signed_amount)
                self.add_debts([i], keep_index, -signed_amount)
                self.add_debts([remove_index], keep_index, signed_amount)

                to_process[list_to_shorten] = to_process[list_to_shorten][1:]
        pass


def main(names):
    dt = DebtTracker(names)
    while True:
        cmd = raw_input("> ")
        dt.parse_command(cmd)

if __name__ == '__main__':
    main(sys.argv[1:])
