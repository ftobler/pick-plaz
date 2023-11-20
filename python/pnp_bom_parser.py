import pnp_bom_parser_eagle



def pnp_bom_parse(pnp, bom):
    parsers = [
        lambda p, b: pnp_bom_parser_eagle.pnp_bom_parse_generic(p, b),
        lambda p, b: pnp_bom_parser_eagle.pnp_bom_parse_eagle(p, b),
    ]
    exceptions = []
    for parser in parsers:
        try:
            return parser(pnp, bom)
        except Exception as e:
            exceptions.append(e)
    raise Exception(exceptions)



def test_bom_pnp(bom_file, pnp_file):
    print("/************************************************************")
    print("test", bom_file, pnp_file)
    with open(pnp_file, "r") as f:
        pnp_str = [s.strip() for s in f.readlines()]
        #pnp_str = f.read().splitlines()
    with open(bom_file, "r") as f:
        bom_str = [s.strip() for s in f.readlines()]
        #bom_str = f.read().splitlines()
    data = pnp_bom_parse(pnp_str, bom_str)
    # print(json.dumps(data, indent=4, sort_keys=True))
    print("************************************************************/")

def test():
    print("automatic testing of BOM parsing")
    import os
    base = "test/bom/"
    #base = "python/test/bom/"
    tests = os.listdir(base)
    for t in tests:
        test = os.path.join(base, t)
        print(test)
        files = os.listdir(test)
        print(files)
        if len(files) != 2:
            raise Exception("wrong number of files")
        bom = None
        pnp = None
        if "bom" in files[0].lower():
            bom = files[0]
            pnp = files[1]
        if "bom" in files[1].lower():
            bom = files[1]
            pnp = files[0]
        if "pnp" in files[0].lower():
            bom = files[1]
            pnp = files[0]
        if "pnp" in files[1].lower():
            bom = files[0]
            pnp = files[1]
        bom = os.path.join(test, bom)
        pnp = os.path.join(test, pnp)
        test_bom_pnp(bom, pnp)


if __name__ == "__main__":
    test()