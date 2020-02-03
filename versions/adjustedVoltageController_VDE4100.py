from versions.SA_preWaitingArrivers import SlottedAloha_preWaitingArrivers

NORM_VOLTAGE = 230


class AdjustedVoltageController(SlottedAloha_preWaitingArrivers):

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
            powerIndex = 20 * Vm / NORM_VOLTAGE - 17.6
            if (powerIndex >= 0.0) & (powerIndex <= 1.0):
                return powerIndex
            elif powerIndex > 1:
                return 1.0
        return 0

    def voltageHighEnough(self, Vm):
        if Vm > 230 * 0.88:
            return True
        else:
            return False
