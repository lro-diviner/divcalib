import scipy.ndimage as nd


def get_sv_selector(df):
    return (df.last_el_cmd >= 75) & \
           (df.last_el_cmd <= 80)


def get_bb_selector(df):
    return (df.last_el_cmd < 5)


def define_sdtype(df):
    df['sdtype'] = 0
    df.loc[get_sv_selector(df), 'sdtype'] = 1
    df.loc[get_bb_selector(df), 'sdtype'] = 2

    df['calib_block_labels'] = nd.label((df.sdtype == 1) |
                                        (df.sdtype == 2))[0]

    df.loc[df.moving == 1, 'sdtype'] = -1

    df['space_block_labels'] = nd.label(df.sdtype == 1)[0]
    df['bb_block_labels'] = nd.label(df.sdtype == 2)[0]

    df['is_spaceview'] = (df.sdtype == 1)
    df['is_bbview'] = (df.sdtype == 2)
    df['is_moving'] = (df.sdtype == -1)
    df['is_calib'] = df.is_spaceview | df.is_bbview


def data_prep(data, hk):
    data['last_az_cmd'] = hk.LAST_AZ_CMD
    data.last_az_cmd = data.last_az_cmd.fillna(method='ffill')
    data['last_el_cmd'] = hk.LAST_EL_CMD
    data.last_az_cmd = data.last_az_cmd.fillna(method='ffill')
    data['moving'] = hk.MOVING
    data.moving = data.moving.fillna(method='ffill')
    define_sdtype(data)
