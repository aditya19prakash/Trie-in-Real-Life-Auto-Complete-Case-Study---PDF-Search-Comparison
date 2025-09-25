class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class AdvancedTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search_prefix(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        return self._collect(node, prefix)

    def _collect(self, node, prefix):
        words = []
        if node.is_end:
            words.append(prefix)
        for ch, nxt in node.children.items():
            words.extend(self._collect(nxt, prefix + ch))
        return words
