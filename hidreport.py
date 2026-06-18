import usb

def hid_set_output_report(dev, report, report_id=0):
    # HID SetReport via control transfer
    dev.ctrl_transfer(
        0x21, 
        9, 
        0x200 + report_id, 0x00,
        report)

def hid_get_input_report(dev, length, report_id=0):
    # HID GetReport via control transfer
    return dev.ctrl_transfer(
        0xA1, 
        1, 
        0x100 + report_id, 0x00,
        length)
