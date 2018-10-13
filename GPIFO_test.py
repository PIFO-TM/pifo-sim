
from Gpifo import GPIFO
import random

NUM_ELEMS = 10
MAX_RANK = 10

elements = ['a', 'b', 'c', 'd', 'e']
groupIDs = [1, 2, None]

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
    test_GPIFO()

if __name__ == '__main__':
    main()

