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

    def getRandomNumber(self, upperLimit, seed):
        """
        returns a random number, which is an interger, greater than 0 but smaller than the given limit.

        :param upperLimit: a positiv integer, which marks the first number that cannot be a possible result.
        :param seed: aa start value for generating random numbers
        :return: a random number
        """
        if not RandomNumber.initialized:
            random.seed(seed)
            RandomNumber.initialized = True
        return random.randrange(0, upperLimit, 1)
