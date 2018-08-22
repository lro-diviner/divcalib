
from diviner import file_utils as fu
from diviner import calib
import numpy as np
import pandas as pd
from diviner import ana_utils as au
from scipy import signal

tstr = '2010020303'
df = fu.open_and_accumulate(tstr)


rdr2 = calib.Calibrator(df)
rdr2.calibrate()

for ch in range(3, 10):
    print("Ch", ch, "det: ", 10)
    cdet = au.CDet(ch, 11)
    det = cdet.mcs

    t1 = '2010-02-03 03:12'
    t2 = '2010-02-03 03:35'

    # calblock = calib.get_calib_blocks(rdr2.df, 'calib')[9]

    sv = calib.get_calib_blocks(df, 'space')[17][det]
    bb = calib.get_calib_blocks(df, 'bb')[9][det]

    detrended = signal.detrend(bb[16:])  # detrending the BB view only
    STD = detrended.std()
    STD2 = sv[16:].std()

    offset = rdr2.offsets[det].iloc[8]
    gain = rdr2.gains[det].iloc[8]

    def calc_NER(SDT, C1, C2, gain, offset):
        R1 = (C1 - offset) * gain
        R2 = (C2 - offset) * gain
        print('R1: {}\nR2: {}'.format(R1, R2))
        return SDT*(R1-R2)/(C1-C2)

    # c1 = sv[16:].mean()
    # c2 = bb[16:].mean()

    # NER = calc_NER(STD, c1, c2, gain, offset)
    NER = STD * gain
    print("NER simple:", STD*gain)

    rbbtable = calib.RBBTable()
    temps = np.linspace(0, 400, 401)
    radiances = rbbtable.get_radiance(temps, ch)
    dR_dT = np.gradient(radiances, np.diff(temps)[0])
    bucket = pd.DataFrame(dR_dT, index=temps, columns=['dR/dT'])
    bucket['R_norm'] = radiances

    bucket['NEdT'] = np.abs(NER / bucket['dR/dT'])

    print("STD:", STD)
    print("STD2:", STD2)
    print("NEdT(300K): ", bucket['NEdT'][300:301].iloc[0])
    print("NEdT(33K): ", bucket['NEdT'][40:41].iloc[0])
    print()
