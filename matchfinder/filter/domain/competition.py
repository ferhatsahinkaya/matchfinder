class Competition:
    def __init__(self, name, matches):
        self.name = name
        self.matches = matches

    def __str__(self):
        return self.name + '\n' + '\n'.join(str(match) for match in self.matches)
