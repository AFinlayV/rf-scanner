def invert_tree(root):
    if root is None:
        return None

    # Swap left and right subtrees
    root["left"], root["right"] = invert_tree(root["right"]), invert_tree(root["left"])

    return root

# Helper function to print the tree (for testing)
def print_tree(root, level=0, prefix="Root: "):
    if root is not None:
        print(" " * (level * 4) + prefix + str(root["val"]))
        print_tree(root["left"], level + 1, "L--- ")
        print_tree(root["right"], level + 1, "R--- ")

# Example usage
if __name__ == "__main__":
    # Constructing a sample binary tree using dictionaries
    tree = {
        "val": 1,
        "left": {
            "val": 2,
            "left": {"val": 4, "left": None, "right": None},
            "right": {"val": 5, "left": None, "right": None}
        },
        "right": {
            "val": 3,
            "left": {"val": 6, "left": None, "right": None},
            "right": {"val": 7, "left": None, "right": None}
        }
    }

    print("Original Tree:")
    print_tree(tree)

    inverted_tree = invert_tree(tree)

    print("\nInverted Tree:")
    print_tree(inverted_tree)
