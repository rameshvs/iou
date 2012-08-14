# iou
## A simple command-line program for tracking debts between people

I wrote this to help keep track of who owes what on a group vacation. Here's
an example:

    $ python iou.py -new
    You can type 'help' (without quotes) at any time for help.
    > help
    Accepted expressions:
        'help':  prints this help info
        'print':  prints out current debts
        'simplify':  simplifies current debts
        'add <new users separated by spaces>': adds users to system
        'clear':  clears all debts (with no warning). use with caution
        '<name> owes <name> <amount>'
        '<name> paid <amount> for <names separated by spaces>':  for splitting
        '<name> paid <amount> for all'
    > add alice bob carol
    > alice owes bob 5
    > bob owes carol 5
    > print
    alice owes bob $5.00
    bob owes carol $5.00
    > simplify
    > print
    alice owes carol $5.00

As seen above, it not only keeps track of who owes what, but also helps simplify
things when there are many different debts.

