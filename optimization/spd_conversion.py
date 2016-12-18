
import flopy


def drop_iface(rec):
    """
    Removes 'iface' column from stress period data recarray
    """
    index = rec.dtype.names.index('iface')
    list_ = rec.tolist()
    for row, i in enumerate(list_):
        list_[row] = list(i)
        del list_[row][index]
        return list_


def prepare_packages_transient(model_object, stress_period_start, stress_period_end):
    """
    Rewrites models spd packages to start/end transient stress_periods
    """

    modflow_spd_packages = {'WEL': flopy.modflow.ModflowWel,
                            'LAK': flopy.modflow.ModflowLak,
                            'RIV': flopy.modflow.ModflowRiv,
                            'CHD': flopy.modflow.ModflowChd,
                            'GHB': flopy.modflow.ModflowGhb}

    print('Reading stress-period-data of the given model object...')
    print(' '.join(['Writing new packages for stress periods ',
                    str(stress_period_start), ':',
                    str(stress_period_end)]))

    for package_name in model_object.get_package_list():
        if package_name in modflow_spd_packages:
            print('Preparing SPD for ' + package_name + ' package')
            package = model_object.get_package(package_name)
            spd = {k: v for
                   k, v in package.stress_period_data.data.items()
                   if stress_period_start <= k <= stress_period_end}

            if 'iface' in spd[stress_period_start].dtype.names:
                print('Removing IFACE from ' + package_name + ' package SPD')
                spd = {k: drop_iface(v) for k, v in spd}

            modflow_spd_packages[package_name] = modflow_spd_packages[package_name](
                model_object,
                stress_period_data=spd
                )

        if package_name == 'DIS':
            print('Preparing DIS package')
            dis = model_object.get_package(package_name)
            perlen = dis.perlen.array[stress_period_start:stress_period_end + 1]
            nstp = dis.nstp.array[stress_period_start:stress_period_end + 1]
            steady = dis.steady.array[stress_period_start:stress_period_end + 1]
            nper = dis.nper
            delc = dis.delc.array
            delr = dis.delr.array
            nlay = dis.nlay
            nrow = dis.nrow
            ncol = dis.ncol
            top = dis.top.array
            botm = dis.botm.array
            laycbd = dis.laycbd.array
            dis_new = flopy.modflow.ModflowDis(model_object, nlay=nlay, nrow=nrow, ncol=ncol,
                                               delr=delr, delc=delc, top=top, steady=steady,
                                               botm=botm, laycbd=laycbd, perlen=perlen, nstp=nstp,
                                               nper=nper)

    return model_object


def prepare_packages_steady(model_object, stress_period):
    """
    Rewrites models packages to single steady stress_period
    """

    modflow_spd_packages = {'WEL': flopy.modflow.ModflowWel,
                            'LAK': flopy.modflow.ModflowLak,
                            'RIV': flopy.modflow.ModflowRiv,
                            'CHD': flopy.modflow.ModflowChd,
                            'GHB': flopy.modflow.ModflowGhb}

    print('Reading stress-period-data of the given model object...')
    print('Writing new packages for a single stress period...')

    for package_name in model_object.get_package_list():
        if package_name in modflow_spd_packages:
            package = model_object.get_package(package_name)
            spd = package.stress_period_data.data[stress_period]
            if 'iface' in spd.dtype.names:
                spd = drop_iface(spd)
            modflow_spd_packages[package_name] = modflow_spd_packages[package_name](
                model_object,
                stress_period_data={0: spd}
                )

        if package_name == 'DIS':
            dis = model_object.get_package(package_name)
            perlen = [dis.perlen.array[stress_period]]
            delc = dis.delc.array
            delr = dis.delr.array
            nlay = dis.nlay
            nrow = dis.nrow
            ncol = dis.ncol
            steady = [True]
            top = dis.top.array
            botm = dis.botm.array
            laycbd = dis.laycbd.array
            dis_new = flopy.modflow.ModflowDis(model_object, nlay=nlay, nrow=nrow, ncol=ncol,
                                               delr=delr, delc=delc, top=top, steady=steady,
                                               botm=botm, laycbd=laycbd, perlen=perlen)

    return model_object