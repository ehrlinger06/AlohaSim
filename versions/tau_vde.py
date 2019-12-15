import versions.adjustedVoltageController_VDE4100 as current


class TauVde(current.AdjustedVoltageController):

    def calcPower(self, inputs):
        available = self.getAtt('available', inputs)
        if available:
            possible_charge_rate = self.getAtt('possible_charge_rate', inputs)
            Vm = self.getAtt('Vm', inputs)
            if self.checkAtt(possible_charge_rate) & self.checkAtt(Vm):
                self.P_new = possible_charge_rate * Vm * self.calculatePowerIndex(Vm)

                return possible_charge_rate * Vm * self.calculatePowerIndex(Vm)
        return 0.0
