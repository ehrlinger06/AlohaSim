from versions.SA_waitingArrivers import BaseLine

NORM_VOLTAGE = 230


class AdjustedVoltageController(BaseLine):

    def calcPower(self, inputs):
        available = self.getAtt('available', inputs)
        if available:
            possible_charge_rate = self.getAtt('possible_charge_rate', inputs)
            Vm = self.getAtt('Vm', inputs)
            if self.checkAtt(possible_charge_rate) & self.checkAtt(Vm):
                return possible_charge_rate * Vm * self.calculatePowerIndex(Vm)
        return 0.0

    def calculatePowerIndex(self, Vm):
        if self.voltageHighEnough(Vm):
            powerIndex = 15.38 * Vm / NORM_VOLTAGE - 14.38
            if (powerIndex >= 0.0) & (powerIndex <= 1.0):
                return powerIndex
            elif powerIndex > 1:
                return 1.0
        return 0

    def voltageHighEnough(self, Vm):
        if Vm > 230 * 0.935:
            return True
        else:
            return False