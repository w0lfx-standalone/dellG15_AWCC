# Model-specific power mode tweaks

def g15_5530_patch(wind):
    del wind.power_modes_dict["USTT_FullSpeed"]

def g15_5520_patch(wind):
    del wind.power_modes_dict["USTT_FullSpeed"]

def g15_5515_patch(wind):
    # AMD models have limited USTT modes
    for mode in ["USTT_Balanced", "USTT_Performance", "USTT_Quiet", "USTT_FullSpeed", "USTT_BatterySaver"]:
        if mode in wind.power_modes_dict:
            del wind.power_modes_dict[mode]

def g15_5511_patch(wind):
    del wind.power_modes_dict["USTT_FullSpeed"]
    del wind.power_modes_dict["USTT_BatterySaver"]
    wind.power_modes_dict["USTT_Cool"] = "0xa2"

def g16_7630_patch(wind):
    del wind.power_modes_dict["USTT_FullSpeed"]
