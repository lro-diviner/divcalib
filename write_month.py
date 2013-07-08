from diviner import file_utils as fu

first_day = '20130301'

pump = fu.L1ADataPump(first_day)

fn_manager = fu.FileName(pump.fnames[0])

df = pump.get_3_hour_block(pump.fnames[0])
pumprdr = fu.RDRDataPump(pump.f)