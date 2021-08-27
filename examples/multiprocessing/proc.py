from multiprocessing import Pool

def f(x):
    return x*x

def main():
    with Pool(5) as p:
        print(p.map(f, [1, 2, 3]))
