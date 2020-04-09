# AlohaSim
A mosaik simulator using the IEEE906 and the FlexEV Simulator 
(https://cnaccgit.fim.uni-passau.de/elco/elco-sim/mosaik-flexev) in version 1.1.4.
The simulator uses parts of the aloha network protocol in a power grid scenario. The Aloha protocol uses waiting as a 
opportunity to spread the activities of the users over a longer period of time to minimize the interference between 
them. 

##Configuration
The simulator takes several parameters, as there is:
* seed: a start value for generating random numbers, the value must be an positive integer and should be a prime numberc(default:c41).
* speed: the amount of amps the participants can use, the value must be a positive integer (default: 96).
* method: the method used in the simulation, must be a string value (default: 'SlottedAloha_participants_VDE_tau').
* run_nr: an id for each run of the simulation, must be an integer (default: 1).
* start: a timestamp in the format 'YYYY-MM-DD HH:mm:ss', which marks the beginning of the simulation 
(default: 2019-11-17 00:00:00)
* end: a timestamp in the format 'YYYY-MM-DD HH:mm:ss', which marks the beginning of the simulation 
(default: 2019-11-24 00:00:00).
All parameter with default settings are obligatory.
 
##Dataoutput
The results of the simulation are stored in an influxdb database or are displayed on the console after the end of the simulation.
* P (double): amount of power (in W) used by a vehicle to charge the battery.
* Q (double): amount of reactive power (in VAr) remains unchanged as it cannot be used for charging.
* S (double): amount of power the transformer outputs into the grid (in VA).
* Vm (double): the voltage level at a connection point to the power grid (in V)
* Vm_10M_average (double): the average voltage level of the last full 10 minute interval.
* available (boolean): a boolean flag, which indicates if the corresponding vehicle is connected to a charger.
* current_soc (double): the current state of charge of a vehicle, after leaving the charging point the value is immediately 
lowered to the value the vehicle will reach the next charger with or return to the same charger again.
* leaving_soc (double): the state of charge from the last time leaving a charger.
* possible_charge_rate (double): the amount of amps the participants can use to charge.
* number of voltage collisions (String): the number of voltage collisions that occurred during the simulation.
* number of steps a voltage collision occurred (String): number of time steps in which a voltage collision occurred.
* number of transformer collisions (String): the number of transformer collisions that occurred during the simulation.
* number of steps a transformer collision occurred (String): number of time steps in which a transformer collision occurred.
* number of collisions overall (String): the number of situations a collision occurred during the simulation.
* number of steps a collision occurred (String): number of time steps in which a collision occurred.

The connection to a running instance of the influxdb is configured in setup.py . All results regarding collisions is 
not stored in the db, but is displayed at the end of the simulation in the console window used to start the simulation.
