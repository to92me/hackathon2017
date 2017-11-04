"""This module is main module for contestant's solution."""

from hackathon.utils.control import Control
from hackathon.utils.utils import ResultsMessage, DataMessage, PVMode, \
    TYPHOON_DIR, config_outs
from hackathon.framework.http_server import prepare_dot_dir


def worker(msg: DataMessage) -> ResultsMessage:
    """TODO: This function should be implemented by contestants."""
    # Details about DataMessage and ResultsMessage objects can be found in /utils/utils.py
    power_reference = 0.0
    load_three = True
    battery_level1 = 0.1
    penalty_load2 = 0.4*60+4
    penalty_load3 = 0.1*60
    current_load_level1 = 4
    current_load_level2 = 3
    battery_level2 = 0.5

    ############# battery managment

    if msg.buying_price == 8 and msg.bessSOC > battery_level1:
        if msg.solar_production > msg.current_load:
            power_reference = - msg.current_load


        else:
            power_reference = (msg.current_load)

#    if msg.selling_price > 0 and msg.bessSOC > battery_level2:

 #       power_reference = -(msg.solar_production - msg.current_load)

    ############# load managment

    if penalty_load3 < 0.3 * msg.current_load*msg.buying_price and msg.current_load > current_load_level1:

        load_three = False

    else:

        load_three = True

    # if penalty_load2 < 0.5 * msg.current_load*msg.buying_price  and msg.current_load > current_load_level1:

    #     load_two = False
    # else:

    #     load_two = True

    load_two = True

    # Dummy result is returned in every cycle here
    return ResultsMessage(data_msg=msg,
                          load_one=True,
                          load_two=load_two,
                          load_three=load_three,
                          power_reference=power_reference,
                          pv_mode=PVMode.ON)


def run(args) -> None:
    prepare_dot_dir()
    config_outs(args, 'solution')

    cntrl = Control()

    for data in cntrl.get_data():
        cntrl.push_results(worker(data))
