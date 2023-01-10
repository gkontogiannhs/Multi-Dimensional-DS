import math
import matplotlib.pyplot as plt


def visualize_rtree(root_node):
    fig, ax = plt.subplots()
    visualize_node(root_node, ax)
    plt.show()

def visualize_node(node, ax):
    x1, y1, x2, y2 = node.mbr.x1, node.mbr.y1, node.mbr.x2, node.mbr.y2
    rect = plt.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='r', facecolor='none')
    ax.add_patch(rect)

    if not node.is_leaf():
        for child in node.children:
            visualize_node(child, ax)


class RTree:
    def __init__(self, min_entries=2, max_entries=4):
        self.min_entries = min_entries
        self.max_entries = max_entries
        self.root = MBRNode(self.min_entries, self.max_entries, parent=None)

    def insert(self, point):
        leaf = self.root.get_leaf_for_point(point)
        leaf.add_point(point)

        if leaf.is_overfull():
            leaf.split()

    def search(self, point):
        return self.root.get_nodes_for_point(point)


class MBRNode:
    def __init__(self, min_entries, max_entries, parent=None):
        self.min_entries = min_entries
        self.max_entries = max_entries
        self.children = []
        self.points = []
        self.mbr = None
        self.parent = parent

    def add_point(self, point):
        self.points.append(point)
        self.mbr = self.get_mbr()

    def is_leaf(self):
        return not self.children

    def is_overfull(self):
        return len(self.points) > self.max_entries

    def get_leaf_for_point(self, point):

        """
        Traverse the R-tree top-down, starting from the root, at each level
        - If there is a node whose directory rectangle contains the point to be inserted, then search the subtree
        - Else choose a node such that the enlargement of its directory rectangle is minimal, then search the subtree
        """

        if self.is_leaf():
            return self
        else:
            return min(self.children, key=lambda node: node.get_mbr_enlargement(point)).get_leaf_for_point(point)

    def get_mbr_enlargement(self, point):

        if not self.mbr: return float('inf')
        else:
            return self.mbr.get_enlargement(Rectangle(point[0], point[1], point[0], point[1]))

    def get_nodes_for_point(self, point):
        if self.is_leaf():
            return [self]
        else:
            nodes = []
            for child in self.children:
                if child.mbr is not None and child.mbr.contains_point(point):
                    nodes.extend(child.get_nodes_for_point(point))
            return nodes


    def update_children(self, old_child, new_child1, new_child2):
        self.children.remove(old_child)
        self.children.append(new_child1)
        self.children.append(new_child2)


    def split(self):
        if self.is_leaf():
            seeds = self.get_seeds()

            new_node1 = MBRNode(self.min_entries, self.max_entries, parent=self)
            new_node1.add_point(seeds[0])

            new_node2 = MBRNode(self.min_entries, self.max_entries, parent=self)
            new_node2.add_point(seeds[1])

            self.children = [new_node1, new_node2]

            for point in self.points:
                if point != seeds[0] and point != seeds[1]:
                    self.add_point_to_best_node(point, new_node1, new_node2)
            
            # remove points
            self.points = []

            if self.parent is not None:
                self.parent.update_children(self, new_node1, new_node2)
                self.parent.update_mbr()


    def add_point_to_best_node(self, point, node1, node2):
        enlargement1 = node1.get_mbr_enlargement(point)
        enlargement2 = node2.get_mbr_enlargement(point)

        if enlargement1 < enlargement2:
            node1.add_point(point)
        else:
            node2.add_point(point)


    def get_seeds(self):
        max_waste = -1
        seeds = []

        for i in range(len(self.points)):
            for j in range(i+1, len(self.points)):
                waste = self.get_waste(self.points[i], self.points[j])
                if waste > max_waste:
                    max_waste = waste
                    seeds = [self.points[i], self.points[j]]

        return seeds


    def get_waste(self, point1, point2):
        combined_mbr = Rectangle(point1[0], point1[1], point1[0], point1[1]).combine(Rectangle(point2[0], point2[1], point2[0], point2[1]))
        return combined_mbr.get_area() - Rectangle(point1[0], point1[1], point1[0], point1[1]).get_area() - Rectangle(point2[0], point2[1], point2[0], point2[1]).get_area()

    
    def get_mbr(self):

        if not self.points: return None

        x_coords = [point[0] for point in self.points]
        y_coords = [point[1] for point in self.points]

        return Rectangle(min(x_coords), min(y_coords), max(x_coords), max(y_coords))


    def update_mbr(self):
        self.mbr = self.get_mbr()
        if self.parent:
            self.parent.update_mbr()
       

class Rectangle:
    def __init__(self, x1, y1, x2, y2):

        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        
    def get_area(self):
        return (self.x2 - self.x1) * (self.y2 - self.y1)
    
    def intersects(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


    def combine(self, other_mbr):

        x1 = min(self.x1, other_mbr.x1)
        y1 = min(self.y1, other_mbr.y1)
        x2 = max(self.x2, other_mbr.x2)
        y2 = max(self.y2, other_mbr.y2)

        return Rectangle(x1, y1, x2, y2)


    def get_enlargement(self, other_mbr):
        if not self.intersects(other_mbr):
            return other_mbr.get_area()
        else:
            x1 = min(self.x1, other_mbr.x1)
            y1 = min(self.y1, other_mbr.y1)
            x2 = max(self.x2, other_mbr.x2)
            y2 = max(self.y2, other_mbr.y2)

            new_mbr = Rectangle(x1, y1, x2, y2)

            # TO CHANGE
            # new_mbr = self.combine(other_mbr)

            return new_mbr.get_area() - self.get_area()
    

    def contains_point(self, point):
        x, y = point
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2
        