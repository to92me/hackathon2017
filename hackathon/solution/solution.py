"""This module is main module for contestant's solution."""

from hackathon.utils.control import Control
from hackathon.utils.utils import ResultsMessage, DataMessage, PVMode, \
    TYPHOON_DIR, config_outs
from hackathon.framework.http_server import prepare_dot_dir
from enum import Enum

globGridStatus = False
counter = 0

last_load_one = True
last_load_two = True
last_load_three = True

battery_level1 = 0.2
penalty_load2 = 0.4 * 60 + 4
penalty_load3 = 0.1 * 60
current_load_level1 = 4.2
current_load_level2 = 4

battery_level2 = 0.3

battery_no_grid_level_1 = 0.4
battery_no_grid_level_2 = 0.3
battery_no_grid_level_3 = 0.2

battery_2_cost_min_level_upper_level = 10.0
battery_2_cost_min_level_lower_level = 1


class PowerSource(Enum):
    """Photo-voltaic panel working mode."""
    grid = 0
    battery = 1
    solar = 2
    solar_battery = 3
    solar_grid = 4
    grid_battery = 5


def calculate_real_load(current_load):
    if last_load_one == True and \
                    last_load_two == True and \
                    last_load_three == True:
        return current_load

    if last_load_one == True and \
                    last_load_two == True and \
                    last_load_three == False:
        return current_load * 1.3

    if last_load_one == True and \
                    last_load_two == False and \
                    last_load_three == False:
        return current_load * 1.7

    if last_load_one == True and \
                    last_load_two == False and \
                    last_load_three == True:
        return current_load * 1.5

def calculate_test_load(load, load_one, load_two, load_three):
    if load_one == True and \
        load_two == True and \
        load_three == True:
        return load

    if load_one == True and \
        load_two == True and \
        load_three == False:
        return  load*0.7

    if load_one == True and \
        load_two == False and \
        load_three == False:
        return load*0.2


def get_power_source(msg: DataMessage, load) -> PowerSource:
    if msg.buying_price == 8 and \
                    msg.solar_production > load:
        return PowerSource.solar

    if msg.buying_price == 8 and \
                    msg.solar_production < load and \
                    msg.bessSOC > battery_level1:
        return PowerSource.solar_battery

    if msg.buying_price == 8 and \
                    msg.solar_production < load and \
                    msg.bessSOC < battery_level1:
        return PowerSource.grid

    if msg.buying_price == 8 and \
                    msg.solar_production == 0 and \
                    msg.bessSOC > battery_level1:
        return PowerSource.battery

    if msg.buying_price < 8 and \
                    msg.bessSOC > battery_2_cost_min_level_upper_level:
                    # msg.solar_production == 0 and \
        return PowerSource.battery

    if msg.buying_price < 8  and \
                    msg.bessSOC < battery_2_cost_min_level_lower_level:
                    # msg.solar_production < load and \
        return PowerSource.grid


def calculate_power_reference(power_reference, load_one, load_two, load_three) -> float:
    if load_three == False and load_two == False:
        power_reference = power_reference * 0.2

    if load_three == False and load_two == True:
        power_reference = power_reference * 0.5

    if load_three == True and load_two == False:
        power_reference = power_reference * 0.7

    return power_reference


def calculate_load_profitability(buying_price, load) -> (bool, bool):
    #load_three = False
    #load_two = False

    if penalty_load3 < 0.3 * load * buying_price: #and load > current_load_level1:

        load_three = False

    else:

        load_three = True

    if penalty_load2 < 0.5 * load * buying_price: # and real_load > current_load_level2:

        load_two = False
    else:

        load_two = True

    return load_two, load_three


def set_loads_and_power_resource(power_source, power_reference, buying_price, real_load, solar_production):
    load_one = True
    load_two = True
    load_three = True

    if power_source == PowerSource.solar:
        load_one = True
        load_two = True
        load_three = True
        power_reference = calculate_power_reference(power_reference, load_one, load_two, load_three)

    if power_source == PowerSource.solar_battery or \
                    power_source == PowerSource.grid_battery or \
                    power_source == PowerSource.solar_grid or \
                    power_source == PowerSource.battery:

        load_one = True

        load_two, load_three = calculate_load_profitability(buying_price, real_load)

        power_reference = -(solar_production - real_load)

        power_reference = calculate_power_reference(power_reference, real_load, load_two, load_three)


    return power_reference, load_one, load_two, load_three



def worker(msg: DataMessage) -> ResultsMessage:
    """TODO: This function should be implemented by contestants."""
    # Details about DataMessage and ResultsMessage objects can be found in /utils/utils.py
    power_reference = 0.0
    load_three = True
    load_two = True
    load_one = True
    pv_mode = PVMode.ON

    global battery_level1
    global penalty_load2
    global penalty_load3
    global current_load_level1
    global current_load_level2

    global globGridStatus, counter
    battery_level2 = 0.5

    global battery_no_grid_level_1
    global battery_no_grid_level_2
    global battery_no_grid_level_3

    global battery_2_cost_min_level_upper_level
    global battery_2_cost_min_level_lower_level

    real_load = calculate_real_load(msg.current_load)

    if msg.grid_status == False or msg.bessOverload == True:

        if msg.bessOverload == True or globGridStatus == True:
            globGridStatus = True

            if (msg.current_load) < 6:

                if msg.bessSOC > battery_no_grid_level_2:
                    load_one = True
                    load_two = True
                    load_three = True
                    power_reference = real_load


                elif msg.bessSOC > battery_no_grid_level_3:
                    load_one = True
                    load_two = True
                    load_three = False
                    power_reference = real_load * 0.7

                elif msg.bessSOC > 0:
                    load_one = True
                    load_two = False
                    load_three = False
                    power_reference = real_load * 0.2

                else:
                    load_three = False
                    load_two = False
                    load_one = False
                    power_reference = 0.0

            elif (msg.current_load * 0.7) < 6:

                if msg.bessSOC > battery_no_grid_level_3:
                    load_one = True
                    load_two = True
                    load_three = False
                    power_reference = real_load * 0.7

                elif msg.bessSOC > 0:
                    load_one = True
                    load_two = False
                    load_three = False
                    power_reference = real_load * 0.2


                else:
                    load_three = False
                    load_two = False
                    load_one = False
                    power_reference = 0.0

            elif (msg.current_load * 0.2) < 6:

                if msg.bessSOC > 0:
                    load_one = True
                    load_two = False
                    load_three = False
                    power_reference = real_load * 0.2

                else:
                    load_three = False
                    load_two = False
                    load_one = False
                    power_reference = 0.0

            else:
                load_three = False
                load_two = False
                load_one = False
                power_reference = 0.0

        if globGridStatus is False:

            if msg.bessSOC > battery_no_grid_level_2:
                load_one = True
                load_two = True
                load_three = True
                power_reference = real_load


            elif msg.bessSOC > battery_no_grid_level_3:
                load_one = True
                load_two = True
                load_three = False
                power_reference = real_load * 0.7

            elif msg.bessSOC > 0:
                load_one = True
                load_two = False
                load_three = False
                power_reference = real_load * 0.2

            else:
                load_three = False
                load_two = False
                load_one = False
                power_reference = 0.0

    else:

        ############# load managment
        globGridStatus = False

        power_source = get_power_source(msg,real_load)

        if power_source ==  PowerSource.solar:
            load_one = True
            load_two = True
            load_three = True
            power_reference = -(msg.solar_production - msg.current_load)

        if power_source == PowerSource.solar_battery:
            load_one = True

            load_two, load_three = calculate_load_profitability(msg.buying_price,  real_load)

            power_reference = -(msg.solar_production -  msg.current_load)

            power_reference = calculate_power_reference(power_reference, load_one, load_two, load_three)


        if power_source == PowerSource.grid_battery:
            load_one = True

            load_two, load_three = calculate_load_profitability(msg.buying_price,  real_load)

            power_reference = -(msg.solar_production -  msg.current_load)

            power_reference = calculate_power_reference(power_reference, load_one, load_two, load_three)

        if power_source == PowerSource.battery:
            load_one = True


            load_two, load_three = calculate_load_profitability(msg.buying_price, real_load)

            power_reference = -(msg.solar_production - msg.current_load)

            power_reference = calculate_power_reference(power_reference, load_one, load_two, load_three)

        if power_source == PowerSource.grid:
            tmp_load_two, tmp_load_three = calculate_load_profitability(msg.buying_price,real_load)

            load_two = tmp_load_two
            load_three = tmp_load_three

            if msg.buying_price < 8:
                power_reference = -6.0
            else:
                power_reference = 0.0
                # load_two = False
                # load_three = False


        if counter > 7100:
            if msg.bessSOC > 0.001:
                power_reference = 4.0
            else:
                power_reference = 0.0
                
            # tmp_load = calculate_test_load(real_load, True, tmp_load_two, tmp_load_three)
            #
            # tmp_power_source = get_power_source(msg, tmp_load)
            #
            # if tmp_power_source != power_source:
            #     power_source = tmp_power_source
            #     power_reference, load_one, load_two, load_three = set_loads_and_power_resource(power_source, power_reference, msg.buying_price, real_load, msg.solar_production)
            #
            # else:
            #     if msg.buying_price < 8:
            #         power_reference = -10.0
            #     else:
            #         power_reference = 0.0
            #     load_three = tmp_load_three
            #     load_two = tmp_load_two
            #     power_reference = calculate_power_reference(power_reference, load_one, load_two, load_three)


        # if msg.grid_status == True:
        #
        #     if penalty_load3 < 0.3 * real_load * msg.buying_price and real_load > current_load_level1:
        #
        #         load_three = False
        #
        #     else:
        #
        #         load_three = True
        #
        #     if penalty_load2 < 0.5 * real_load * msg.buying_price and real_load > current_load_level2:
        #
        #         load_two = False
        #     else:
        #
        #         load_two = True

        # if msg.buying_price == 8 and \
        #                 msg.solar_production > real_load:
        #     power_reference = -(msg.solar_production - real_load)
        #
        # if msg.buying_price == 8 and \
        #                 msg.solar_production < real_load and \
        #                 msg.bessSOC > battery_level1:
        #     power_reference = -(msg.solar_production - real_load)
        #
        # if msg.buying_price == 8 and \
        #                 msg.solar_production < real_load and \
        #                 msg.bessSOC < battery_level1:
        #     power_reference = 0.0
        #     pass
        #
        # if msg.buying_price < 8 and \
        #                 msg.solar_production < real_load and \
        #                 msg.bessSOC > battery_2_cost_min_level_upper_level:
        #     power_reference = real_load
        #
        # if msg.buying_price < 8 and \
        #                 msg.solar_production < real_load and \
        #                 msg.bessSOC < battery_2_cost_min_level_lower_level:
        #     power_reference = -10.0
        #
        # if load_three == False and load_two == False:
        #     power_reference = power_reference * 0.2
        #
        # if load_three == False and load_two == True:
        #     power_reference = power_reference * 0.5
        #
        # if load_three == True and load_two == False:
        #     power_reference = power_reference * 0.7



        # if counter%10:
        # print ("counter is ", counter, " , global flag is ", globGridStatus, "overload is ", msg.bessOverload)

    last_load_one = load_one
    last_load_two = load_two
    last_load_three = load_three

    counter = counter + 1
    # Dummy result is returned in every cycle here
    return ResultsMessage(data_msg=msg,
                          load_one=load_one,
                          load_two=load_two,
                          load_three=load_three,
                          power_reference=power_reference,
                          pv_mode=pv_mode)


def run(args) -> None:
    prepare_dot_dir()
    config_outs(args, 'solution')

    cntrl = Control()

    for data in cntrl.get_data():
        cntrl.push_results(worker(data))


        # if msg.buying_price == 8:
        #     if msg.bessSOC > battery_level1:
        #         pv_mode = PVMode.OFF
        #         if msg.solar_production > msg.current_load:
        #             power_reference = msg.current_load - msg.solar_production
        #         else:
        #             power_reference = msg.solar_production - msg.current_load
        #     else:
        #         pv_mode = PVMode.ON
        #         if msg.solar_production > msg.current_load:
        #             power_reference = msg.current_load - msg.solar_production
        #         else:
        #             power_reference = 0.0

        # if msg.buying_price < 8:
        #     if(msg.solar_production > msg.current_load):
        #         pv_mode = False
        #
        #
        #
        #
        #     else:
        #         if(msg.bessSOC > battery_2_cost_min_level):
        #             power_reference = msg.current_load
        #         else:
        #             power_reference = -msg.current_load



        # else:
        #
        # if msg.buying_price == 8:
        #    if msg.solar_production > msg.current_load:
        #         pv_mode = PVMode.OFF




        #    if msg.selling_price > 0 and msg.bessSOC > battery_level2:

        #       power_reference = -(msg.solar_production - msg.current_load)




        ############# battery

        # if msg.bessOverload == True or globGridStatus == True:
        #     # if (msg.current_load * 0.2) > 6:
        #     # load_three = False
        #     # load_two = False
        #     # load_one = False
        #
        #     # elif (msg.current_load * 0.5) > 6:
        #     #     load_three = False
        #     #     load_two = False
        #
        #     # else:
        #     #     load_three = False
        #     load_three = False
        #     load_two = False
        #     globGridStatus = True
        #
        #     print("-------------------------------------------------------------------------------------------")
        #
        #     return ResultsMessage(data_msg=msg,
        #                           load_one=True,
        #                           load_two=False,
        #                           load_three=False,
        #                           power_reference=msg.current_load*0.2,
        #                           pv_mode=pv_mode)
