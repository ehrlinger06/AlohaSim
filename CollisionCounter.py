

class CollisionCounter():
    __instance = None
    initialized = False
    collisionsDict = {}

    @staticmethod
    def getInstance():
        if CollisionCounter.__instance is None:
            CollisionCounter()
        return CollisionCounter.__instance

    def __init__(self):
        if CollisionCounter.__instance is not None:
            raise Exception("Singleton already present")
        else:
            CollisionCounter.__instance = self

    def addCollision(self, step):
        # when key is present
        if step in CollisionCounter.collisionsDict:
            CollisionCounter.collisionsDict[step] = CollisionCounter.collisionsDict[step] + 1
        else:
            # when key is not present
            CollisionCounter.collisionsDict[step] = 1

    def printResults(self):
        # number of steps in which a collisions occurred
        print("number of steps in which a collisions occurred:", len(CollisionCounter.collisionsDict))
        numberOfCollisions = 0
        for numb in CollisionCounter.collisionsDict.values():
            numberOfCollisions += numb
        print("number of collisions:", numberOfCollisions)

    def getCollStepsNumber(self):
        return len(CollisionCounter.collisionsDict)

    def getCollsNumber(self):
        numberOfCollisions = 0
        for numb in CollisionCounter.collisionsDict.values():
            numberOfCollisions += numb
        return numberOfCollisions