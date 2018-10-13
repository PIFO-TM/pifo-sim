
import sys

class GPIFO_tree(object):
    """
    Tree of group-based PIFOs
    """
    def __init__(self, shape):
        """
        Inputs:
            - shape : the shape of the tree
        """
        self.shape = shape

class GPIFO(object):
    """
    Group-based PIFO implementation.
    Stores items in sorted order based on packet or group rank.
    """
    def __init__(self):
        # the items to sort - can be either packets or FIFOs
        self.items = PriorityQ()

        # table to lookup FIFOs based on groupID
        self.group_table = {}

    def insert(self, elem, rank, groupID=None):
        """
        Insert an element into the GPIFO.
        Inputs:
          - elem : the new element to insert into the GPIFO
          - rank : the rank to use for scheduling
          - groupID : if None then elem is scheduled individually.
                   Otherwise, the groupID indicates which FIFO to
                   insert the element into. If the groupID is currently
                   unused then a new FIFO is allocated.
        """
        if groupID is None:
            # insert the packet
            self.items.push([rank, elem])
        else:
            # insert into FIFO group
            if groupID in self.group_table.keys():
                # FIFO group already exists so insert into it
                elem_list = self.group_table[groupID]
                # Update the FIFO's rank and push the element
                elem_list[0] = rank
                elem_list[1].push(elem)
                # re-sort the items
                self.items.sort()
            else:
                # allocate new FIFO and insert
                fifo = FIFO(groupID)
                fifo.push(elem)
                elem_list = [rank, fifo]
                self.group_table[groupID] = elem_list
                self.items.push(elem_list)

    def remove(self):
        """
        Remove the head element (smallest rank) from the GPIFO
        """
        if len(self.items) > 0:
            head_list = self.items.get_min()
            head_rank = head_list[0]
            head_elem = head_list[1]
            if type(head_elem) == FIFO:
                head = head_elem.pop()
                if len(head_elem) == 0:
                    # only remove the head element if the FIFO is empty
                    self.items.pop()
                    # delete the entry from the group_table
                    del self.group_table[head_elem.ID]
            else: # is a packet
                head = head_elem
                self.items.pop()
            return head
        else:
            print >> sys.stderr, "ERROR: GPIFO.remove: cannot remove from empty GPIFO"
            sys.exit(1)

    def __str__(self):
        """ Return string representation of GPIFO
        """
        elements = self.items.get_items()
        result = ''
        for elem_list in elements:
            result += '{} : {}\n'.format(str(elem_list[0]), str(elem_list[1]))
        return result

class PriorityQ(object):
    """
    Simple Priority queue - can't use heap because it doesn't maintain FIFO order
    for elements with the same rank
    """
    def __init__(self):
        self.items = []
    def push(self, elem):
        """
        Add an element to the PriorityQ
        """
        self.items.append(elem)
        self.items.sort()
    def pop(self):
        """
        Remove element with highest priority
        """
        if len(self.items) > 0:
            head = self.items[0]
            self.items = self.items[1:]
            return head
        else:
            print >> sys.stderr, "ERROR: PriorityQ.pop: cannot pop from empty PriorityQ"
            sys.exit(1)
    def sort(self):
        """ Resort elements
        """
        self.items.sort()
    def get_min(self):
        """
        Check the min element
        """
        if len(self.items) > 0:
            return self.items[0]
        else:
            return None
    def get_items(self):
        return self.items
    def __len__(self):
        return len(self.items)

class FIFO(object):
    """
    Simple FIFO queue implementation
    """
    def __init__(self, ID):
        self.ID = ID
        self.items = []
    def push(self, data):
        self.items.append(data)
    def pop(self):
        if len(self.items) > 0:
            head = self.items[0]
            self.items = self.items[1:]
            return head
        else:
            print >> sys.stderr, "ERROR: FIFO.pop: cannot remove from empty FIFO"
            sys.exit(1)
    def __len__(self):
        return len(self.items)
    def __str__(self):
        return '{} - ID: {}'.format(str(self.items), self.ID)


