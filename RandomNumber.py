import random

class RandomNumber():
    __instance = None
    initialized = False

    @staticmethod
    def getInstance():
        if RandomNumber.__instance is None:
            RandomNumber()
        return RandomNumber.__instance

    def __init__(self):
        if RandomNumber.__instance is not None:
            raise Exception("Singleton already present")
        else:
            RandomNumber.__instance = self

    def getRandomNumber(self, upperLimit):
        if not RandomNumber.initialized:
            random.seed(41)
            RandomNumber.initialized = True
        return random.randrange(0, upperLimit, 1)
