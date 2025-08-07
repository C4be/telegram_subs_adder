import random as rnd

def get_name(names_dir: str = 'names.txt') -> str:
    with open(names_dir, 'r') as f:
        names = f.readline().strip().split(',')
    return rnd.choice(names)

