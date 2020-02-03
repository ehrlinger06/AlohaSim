import random

random.seed(41)
one = 0
two = 0
three = 0
four = 0
five = 0
six = 0
seven = 0
eight = 0
nine = 0
for i in range(100):
    numb = random.randrange(1, 10, 1)
    if numb == 1:
        one += 1
    elif numb == 2:
        two += 1
    elif numb == 3:
        three += 1
    elif numb == 4:
        four += 1
    elif numb == 5:
        five += 1
    elif numb == 6:
        six += 1
    elif numb == 7:
        seven += 1
    elif numb == 8:
        eight += 1
    elif numb == 9:
        nine += 1

print('one:', one)
print('two:', two)
print('three:', three)
print('four:', four)
print('five:', five)
print('six:', six)
print('seven:', seven)
print('eight:', eight)
print('nine:', nine)
