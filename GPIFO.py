
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
        self.nodes = {} # map node ID to node object
        self.root = self.make_tree(shape, None)

    def make_tree(self, shape, parent):
        """
        Create a tree of GPIFOs
        Inputs:
            shape : shape of tree
                    e.g. [2, 0, 1]
                    e.g. [6, [4, 0, 1], [5, 2, 3]]
        """
        if len(shape) == 0:
            return None
        elif len(shape) > 0:
            rootID = shape[0]
            root = GPIFO_node(rootID, parent)
            self.nodes[rootID] = root
            for n in shape[1:]:
                if type(n) == list:
                    node = self.make_tree(n, root)
                else:
                    node = GPIFO_node(n, root)
                self.nodes[node.ID] = node
                root.add_child(node) 
            return root

    def insert(self, elem, ranks, groupIDs, nodeID):
        """
        Insert an element into the tree.
        Inputs:
            - elem : the element to insert
            - ranks : the ranks to use for each insertion. ranks[0] is used for nodeID
            - groupIDs : the groupIDs to use for each insertion. groupIDs[0] is used for nodeID
            - nodeID : the leaf node ID to insert into
        """
        leaf_node = self.nodes[nodeID]
        if len(leaf_node.children) != 0:
            print >> sys.stderr, "ERROR: GPIFO_tree.insert: cannot insert into non-leaf node {}".format(nodeID)
            sys.exit(1)
        leaf_node.insert(elem, ranks, groupIDs)

    def remove(self):
        """
        Remove an element from the tree
        """
        elem = self.root.remove()
        return elem

    def __str__(self):
        return str(self.root)

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

    def __str__(self, level=0):
        """ Return string representation of GPIFO
        """
        elements = self.items.get_items()
        result = ''
        for elem_list in elements:
            result += '\t'*level + '{} : {}\n'.format(str(elem_list[0]), str(elem_list[1]))
        return result

class GPIFO_node(GPIFO):
    """
    A node of the GPIFO_tree
    """
    def __init__(self, ID, parent):
        self.ID = ID
        self.parent = parent
        self.children = []
        super(GPIFO_node, self).__init__()

    def add_child(self, node):
        self.children.append(node)

    def insert(self, elem, ranks, groupIDs):
        """
        Insert elem into the node, then continue insertions towards the root
        """
        if len(ranks) != len(groupIDs) or len(ranks) == 0 or len(groupIDs) == 0:
            print >> sys.stderr, "ERROR: GPIFO_node.insert: invalid ranks and/or groupIDs:\n{}\n{}".format(ranks, groupIDs)
            sys.exit(1)
        super(GPIFO_node, self).insert(elem, ranks[0], groupIDs[0])
        if self.parent is not None:
            self.parent.insert(self.ID, ranks[1:], groupIDs[1:])

    def remove(self):
        """
        Remove an element from the node and recursively remove from children until the leaf node is reached.
        Return the element removed from the leaf
        """
        elem = super(GPIFO_node, self).remove()
        if len(self.children) > 0:
            for child in self.children:
                if child.ID == elem:
                    return child.remove()
            print >> sys.stderr, "ERROR: GPIFO_node.remove: unknown child {} for node {}".format(elem, self.ID)
            sys.exit(1)
        else:
            return elem

    def __str__(self, level=0):
        result = 'Node {}:\n'.format(self.ID)
        result += super(GPIFO_node, self).__str__(level) + '\n'
        for child in self.children:
            result += child.__str__(level+1)
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


