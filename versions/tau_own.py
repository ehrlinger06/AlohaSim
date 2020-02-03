from versions.SA_preWaitingArrivers import SlottedAloha_preWaitingArrivers

NORM_VOLTAGE = 230


class TauOwn(SlottedAloha_preWaitingArrivers):

    def calcPower(self, inputs):
        available = self.getAtt('available', inputs)
        if available:
            possible_charge_rate = self.getAtt('possible_charge_rate', inputs)
            Vm = self.getAtt('Vm', inputs)
            if self.checkAtt(possible_charge_rate) & self.checkAtt(Vm):
                self.P_new = possible_charge_rate * Vm * self.calculatePowerIndex(Vm)
                if self.P_old > self.P_new:
                    difference = (self.P_old - self.P_new) * 0.632
                    self.P_out = self.P_old - difference
                else:
                    difference = (self.P_new - self.P_old) * 0.632
                    self.P_out = self.P_old + difference
                    self.P_old = self.P_out
                return self.P_out
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
