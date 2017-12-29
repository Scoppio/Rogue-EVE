import random

# from http://www.geocities.com/anvrill/names/cc_goth.html
PLACES = ['Adara', 'Adena', 'Adrianne', 'Alarice', 'Alvita', 'Amara', 'Ambika', 'Antonia', 'Araceli', 'Balandria', 'Basha',
'Beryl', 'Bryn', 'Callia', 'Caryssa', 'Cassandra', 'Casondrah', 'Chatha', 'Ciara', 'Cynara', 'Cytheria', 'Dabria', 'Darcei',
'Deandra', 'Deirdre', 'Delores', 'Desdomna', 'Devi', 'Dominique', 'Drucilla', 'Duvessa', 'Ebony', 'Fantine', 'Fuscienne',
'Gabi', 'Gallia', 'Hanna', 'Hedda', 'Jerica', 'Jetta', 'Joby', 'Kacila', 'Kagami', 'Kala', 'Kallie', 'Keelia', 'Kerry',
'Kerry-Ann', 'Kimberly', 'Killian', 'Kory', 'Lilith', 'Lucretia', 'Lysha', 'Mercedes', 'Mia', 'Maura', 'Perdita', 'Quella',
'Riona', 'Safiya', 'Salina', 'Severin', 'Sidonia', 'Sirena', 'Solita', 'Tempest', 'Thea', 'Treva', 'Trista', 'Vala', 'Winta',
'Lothlorien', 'Thranduil', 'Legolas', 'Gloin', 'Glorfindel', 'Arwen', 'Aratorn', 'Boromir', 'Arandelle', 'Aragorn', 
'Elizabeth', 'Topogigio', 'Deimos', 'Boceta', 'Corbett', 'Markov', 'Ninive', 'Rohirin']

###############################################################################
# Markov Name model
# A random name generator, by Peter Corbett
# http://www.pick.ucam.org/~ptc24/mchain.html
# This script is hereby entered into the public domain
###############################################################################


class Mdict(object):
    def __init__(self):
        self.d = {}

    def __getitem__(self, key):
        if key in self.d:
            return self.d[key]
        else:
            raise KeyError(key)

    def add_key(self, prefix, suffix):
        if prefix in self.d:
            self.d[prefix].append(suffix)
        else:
            self.d[prefix] = [suffix]

    def get_suffix(self,prefix):
        l = self[prefix]
        return random.choice(l)  


class MarkovNameGenerator(object):
    """
    A name from a Markov chain
    """
    def __init__(self, size = 4):
        """
        Building the dictionary
        """
        if size > 10 or size < 1:
            raise AttributeError("Chain length must be between 1 and 10, inclusive")
    
        self.mcd = Mdict()
        old_names = []
        self.size = size
    
        for l in PLACES:
            l = l.strip()
            old_names.append(l)
            s = " " * size + l
            for n in range(0,len(l)):
                self.mcd.add_key(s[n:n+size], s[n+size])
            self.mcd.add_key(s[len(l):len(l)+size], "\n")

    def __len__(self):
        return self.size

    def request_name(self):
        """
        New name from the Markov chain
        """
        prefix = " " * self.size
        name = ""
        suffix = ""
        while True:
            suffix = self.mcd.get_suffix(prefix)
            if suffix == "\n" or len(name) > 9:
                break
            else:
                name = name + suffix
                prefix = prefix[1:] + suffix
        return name.capitalize()