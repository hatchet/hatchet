import hatchet as ht
if __name__ == "__main__":
    gf = ht.GraphFrame.from_hpctoolkit("/Users/carter_lewis/Desktop/hatchet-carter/hatchet/hatchet/tests/data/hpctoolkit-cpi-database")
    print(gf.tree(depth=1))
    print(gf.tree(depth=3))
    print(gf.tree(depth=10))
    print(gf.tree())
    print(gf.dataframe)
    #print(gf.tree(depth=11))
    #ht.test_tree(gf)
    
    #print(gf.tree(depth=4, metric_column = ["time", "time (inc)"]))

    #print(gf.tree())
    