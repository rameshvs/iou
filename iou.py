from __future__ import division
from __future__ import print_function

import collections
import math
import sys
import numpy as np

try:
    from IPython.core.debugger import Tracer
    debug_here = Tracer()
except:
    debug_here = lambda : None

USAGE = """Usage:
%s -load <filename>
%s -new"""

# version 0.3: graph simplification works, minimal input checking/error handling
# TODO gentler handling of invalid names
# TODO can syntax be made cleaner?
SAVE_VERSION = '0.3'
HELP_STRING = """\
  Accepted expressions:
    'help':  prints this help info
    'print':  prints out current debts
    'simplify':  simplifies current debts
    'add <new users separated by spaces>': adds users to system
    'clear':  clears all debts (with no warning). use with caution
    '<name> owes <name> <amount>'
    '<name> paid <amount> for <names separated by spaces>':  for splitting
    '<name> paid <amount> for all'"""

def load_from_file(filename):
    with open(filename) as f:
        version = f.readline()[:-1]
        if version != SAVE_VERSION:
            print("Different (incompatible) versions used between saving and loading. Possible data corruption, but I'll try to load anyway.")
        names = f.readline().split()
        numbers = f.readlines()
        debt_lists = []
        for row in numbers:
            debt_lists.append(map(float,row.split()))

    print("Successfully loaded from %s. Current users are %s"%(filename, ', '.join(names)))
    return DebtTracker(names, debt_lists)


class DebtTracker(object):

    def __init__(self, names=None, debt_graph=None):

        # self.debt_graph is a skew-symmetric matrix tracking debts:
        # if debt_graph[i,j] = a, then i owes j $a, and debt_graph[j,i] = -a.
        if names is None and debt_graph is None:
            self.names = []
            self.debt_graph = np.zeros([0,0])
            self.N = 0
        elif names is not None and debt_graph is not None:
            # loaded from file
            self.names = names
            self.N = len(names)
            for name in self.names:
                self.check_name(name)
            self.debt_graph = np.array(debt_graph)
            assert np.allclose(self.debt_graph,-self.debt_graph.T)
        else:
            raise ValueError("Invalid initialization. Need both names+debt graph, or neither")

        self.command_handler = collections.defaultdict(lambda : self.handle_debt_command)

        self.command_handler['print']    = lambda tokens: self.print_debts()
        self.command_handler['help']     = lambda tokens: self.print_help()
        self.command_handler['debug']    = lambda tokens: debug_here()
        self.command_handler['simplify'] = lambda tokens: self.simplify_debts()
        self.command_handler['add']      = self.handle_add_command
        self.command_handler['clear']    = lambda tokens: self.handle_clear_command()
        self.command_handler['save']     = lambda tokens: self.dump_to_file(tokens[1])
        self.command_handler['quit']     = lambda tokens: sys.exit(0)

        print("You can type 'help' (without quotes) at any time for help.")

    def check_name(self, name):
        # since we use spaces to tokenize input, we can't have spaces in
        # names. we also can't have any of the reserved keywords used as names
        assert ' ' not in name
        assert name not in ['help','print','add','debug','all','simplify','save','quit']

    def dump_to_file(self, filename):
        """
        Dumps the name list and debt matrix to a plaintext file.
        Truncates debts to 2 decimal places, sacrificing precision for file readability
        """
        out_string = SAVE_VERSION
        out_string += '\n' + ' '.join(self.names)
        for row in self.debt_graph:
            row_as_string = ' '.join(map(lambda num: '%0.2f'%num, row))
            out_string += '\n' + row_as_string
        with open(filename,'w') as f:
            f.write(out_string)


    def add_debts(self, debtors, lender, amount):
        # each debtor in debtors owes exactly amount to lender
        added_edges = np.zeros([self.N,self.N])
        for debtor in debtors:
            added_edges[debtor,lender] = amount
            added_edges[lender,debtor] = -amount
        self.debt_graph += added_edges

    def print_help(self):
        print(HELP_STRING)

    def _lookup(self, name):
        """ For internal use only """
        return self.names.index(name)

    def parse_command(self, command):
        tokens = command.strip().lower().split(' ')
        try:
            self.command_handler[tokens[0]](tokens)
        except KeyError:
            print("** Unknown/unparseable command, please try again")

    def handle_debt_command(self, tokens):
        if tokens[1] == 'owes':
            (debtor,_,lender,amount_string) = tokens
            self.add_debts([self._lookup(debtor)], self._lookup(lender), float(amount_string))
        elif tokens[1] == 'paid':
            (lender,_,total_amount_string) = tokens[:3]
            debtors_raw = tokens[4:]
            if debtors_raw == ['all']:
                debtors = range(self.N)
                debtors.remove(self._lookup(lender))
            else:
                debtors = map(self._lookup, debtors_raw)
            # add 1 because part of what the lender paid was for himself/herself too
            amount = float(total_amount_string) / (len(debtors) + 1)
            self.add_debts(debtors, self._lookup(lender), amount)
        else:
            print("** Debt commands must contain 'owes' or 'paid'")

    def handle_add_command(self, tokens):
        for cname in tokens[1:]:
            name = cname.lower()
            self.check_name(name)
            self.names.append(name)

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
                    raise ValueError("Number was not > < or = 0. nan issue?")
                print("%s owes %s $%0.2f"%(self.names[debtor],self.names[lender],abs(amount)))

    def simplify_debts(self):
        # tries to sparsify debt graph. for example, if A owes B $1 and B owes
        # C $1, then this can be simplified to "A owes C $1".

        # in terms of the graph, this makes sure every node is either a source
        # or a sink. Any 'flow' passing through a node can be rerouted around
        # it.

        for i in xrange(self.N):
            row = self.debt_graph[i,:]
            sign = np.sum(row)
            # if the flow in is greater than the flow out, then this node is a
            # sink, and we want to _remove_ all out flows and _keep_ the
            # remaining in flows. vice versa for source nodes
            if sign >= 0:
                to_remove = np.flatnonzero(row < 0)
                to_keep = np.flatnonzero(row > 0)
            elif sign < 0:
                to_remove = np.flatnonzero(row > 0)
                to_keep = np.flatnonzero(row < 0)

            to_process = [to_remove,to_keep]

            # keep removing until this node is either a source or a sink
            while len(to_process[0]) > 0:
                (remove_index, keep_index) = zip(*to_process)[0]
                (removing,keeping) = (row[remove_index], row[keep_index])

                # between the current 'in' and the current 'out', we want
                # to remove the smaller of the two
                if abs(removing) <= abs(keeping):
                    # it's important that the = sign be on the first case, since
                    # otherwise we may unnecessarily stay in the while loop, and
                    # index extraction will fail
                    amount = removing
                    list_to_shorten = 0
                else:
                    amount = keeping
                    list_to_shorten = 1

                signed_amount = math.copysign(amount,keeping)

                # removal is accomplished by rerouting: we eliminate the
                # debts involving this node and replace them with a debt
                # that "goes around" this node
                self.add_debts([i], remove_index, signed_amount)
                self.add_debts([i], keep_index, -signed_amount)
                self.add_debts([remove_index], keep_index, signed_amount)

                # now that we've eliminated one of this node's
                # debtors/creditors, we can remove that one from the list
                to_process[list_to_shorten] = to_process[list_to_shorten][1:]


def main(argv):
    if len(sys.argv) == 3 and sys.argv[1] == '-load':
        dt = load_from_file(argv[2])
    elif len(sys.argv) == 2 and sys.argv[1] == '-new':
        dt = DebtTracker()
    else:
        print(USAGE % (argv[0],argv[0]))
        sys.exit(1)
    while True:
        cmd = raw_input("> ")
        dt.parse_command(cmd)

if __name__ == '__main__':
    main(sys.argv)
