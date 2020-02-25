testOuter = {}
testInner1 = {
    "Hallo": 1
}
testInner2 = {
    "Hallo": 2
}
testInner3 = {
    "Hallo": 3
}
testInner4 = {
    "Hallo": 4
}
testInner5 = {
    "Hallo": 5
}
testInner5 = {
    "Hallo": 5
}
testOuter["test"] = {}
testOuter["test"][2] = testInner1
testOuter["test"][3] = testInner2
testOuter["versuch"] = {}
testOuter["versuch"][1] = testInner3

print()

for string in testOuter.keys():
    print(string)
    for val in testOuter[string].values():
        print(val)
