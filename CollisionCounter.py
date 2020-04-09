

class CollisionCounter():
    __instance = None
    initialized = False
    collisionsDictVolt = {}
    collisionsDictTrafo = {}
    timingDict = {}
    counter = 0

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

    def addCollisionVolt(self, step):
        # when key is present
        if step in CollisionCounter.collisionsDictVolt:
            CollisionCounter.collisionsDictVolt[step] = CollisionCounter.collisionsDictVolt[step] + 1
        else:
            # when key is not present
            CollisionCounter.collisionsDictVolt[step] = 1

    def addCollisionTrafo(self, step):
        # when key is present
        if step in CollisionCounter.collisionsDictTrafo:
            CollisionCounter.collisionsDictTrafo[step] = CollisionCounter.collisionsDictTrafo[step] + 1
        else:
            # when key is not present
            CollisionCounter.collisionsDictTrafo[step] = 1

    def waitingTimeCalculated(self, step):
        if step in CollisionCounter.timingDict:
            CollisionCounter.timingDict[step] = CollisionCounter.timingDict[step] + 1
        else:
            # when key is not present
            CollisionCounter.timingDict[step] = 1

    def riseCounter(self):
        CollisionCounter.counter += 1

    def printResults(self):
        # number of steps in which a collisions occurred
        print("number of steps in which a  voltage collisions occurred:", len(CollisionCounter.collisionsDictVolt))
        numberOfCollisionsVolt = 0
        for numb in CollisionCounter.collisionsDictVolt.values():
            numberOfCollisionsVolt += numb
        print("number of voltage collisions:", numberOfCollisionsVolt)
        print("number of steps in which a trafo collisions occurred:", len(CollisionCounter.collisionsDictTrafo))
        numberOfCollisionsTrafo = 0
        for numb in CollisionCounter.collisionsDictTrafo.values():
            numberOfCollisionsTrafo += numb
        print("number of Trafo collisions:", numberOfCollisionsTrafo)
        print("number of situations a collision occurred:", CollisionCounter.counter)
        print("number of steps in which a waitingTime was calculated:", len(CollisionCounter.timingDict))
        numberOfTimings = 0
        for numb in CollisionCounter.timingDict.values():
            numberOfTimings += numb
        print("number of waitingTimes:", numberOfTimings)



    def getCollStepsNumber(self):
        return len(CollisionCounter.collisionsDict)

    def getCollsNumber(self):
        numberOfCollisions = 0
        for numb in CollisionCounter.collisionsDict.values():
            numberOfCollisions += numb
        return numberOfCollisions