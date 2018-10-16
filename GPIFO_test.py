
from GPIFO import GPIFO_tree, GPIFO
import random

NUM_ELEMS = 5
MAX_RANK = 10

elements = ['a', 'b', 'c', 'd', 'e']
groupIDs = [1, 2, None]

def make_ranks(num_ranks):
    ranks = []
    for i in range(num_ranks):
        r = random.randint(0, MAX_RANK)
        ranks.append(r)
    return ranks

def make_groupIDs(num_groupIDs):
    IDs = []
    for i in range(num_groupIDs):
        groupID = random.choice(groupIDs)
        IDs.append(groupID)
    return IDs

def test_GPIFO_tree():
    depth = 2
    tree = GPIFO_tree([2, 0, 1])
    for i in range(NUM_ELEMS):
        elem = random.choice(elements)
        ranks = make_ranks(depth)
        gIDs = make_groupIDs(depth)
        leaf_node = random.randint(0, 1)
        print 'Inserting element: {} -- ranks: {} -- groupIDs: {} -- leaf_node: {}'.format(elem, ranks, gIDs, leaf_node)
        tree.insert(elem, ranks, gIDs, leaf_node)
    print 'Current tree state:\n{}'.format(str(tree))
    for i in range(NUM_ELEMS):
        head = tree.remove()
        print 'Removed element: {}'.format(head)
    print 'FINISHED!'   

def test_GPIFO():
    gpifo = GPIFO()
    for i in range(NUM_ELEMS):
        elem = random.choice(elements)
        rank = random.randint(0, MAX_RANK)
        groupID = random.choice(groupIDs)
        print 'Inserting element: {} -- rank: {} -- groupID: {}'.format(elem, rank, groupID)
        gpifo.insert(elem, rank, groupID)
    print 'Current GPIFO state:\n{}'.format(str(gpifo))
    for i in range(NUM_ELEMS):
        head = gpifo.remove()
        print 'Removed element: {}'.format(head)
    print 'FINISHED!'

def main():
    #test_GPIFO()
    test_GPIFO_tree()

if __name__ == '__main__':
    main()

