from influxdb import DataFrameClient

import os
from multiprocessing import Pool
import pandas as pd  # hier
import numpy as np
from datetime import timedelta
import matplotlib.pyplot as plt  # hier
import seaborn as sns  # hier

# set seaborn style on matplotlib
sns.set()

n_jobs = 1

# Instantiate the connection to the InfluxDB client
host = 'localhost'
port = 8086
user = 'root'
password = 'root'
dbname = 'aloha_test_10'
run_id = 'SlottedAloha_participants_VDE_tau_trafo2'

plot_folder = 'C:/Users/MJE17/OneDrive/Dokumente/plots/SA_participants/SA_participants_VDE_tau_trafo'



def get_available(client, bind_params):
    available_query = 'SELECT distinct("value") FROM "available" WHERE ("run_id" = $run_id AND "method" = $method AND "component" = $component_id AND "run_nr" = $run_nr AND "value" = True) GROUP BY time(1m)'
    available_res = client.query(available_query, bind_params=bind_params)
    available_df = available_res.get('available', None)
    return None if available_df is None else available_df.rename(columns={'distinct': 'available'})


def get_soc(client, bind_params):
    soc_query = 'SELECT distinct("value") FROM "current_soc" WHERE ("run_id" = $run_id AND "method" = $method AND "component" = $component_id AND "run_nr" = $run_nr) GROUP BY time(1m)'
    soc_res = client.query(soc_query, bind_params=bind_params)
    soc_df = soc_res.get('current_soc', None)
    return None if soc_df is None else soc_df.rename(columns={'distinct': 'soc'})


def get_power(client, bind_params):
    power_query = 'SELECT distinct("value") FROM "P" WHERE ("run_id" = $run_id AND "method" = $method AND "component" = $component_id AND "run_nr" = $run_nr) GROUP BY time(1m)'
    power_res = client.query(power_query, bind_params=bind_params)
    power_df = pd.DataFrame(power_res['P'])
    power_df = power_df.rename(columns={'distinct': 'power'})
    return power_df


def get_leaving_soc(client, bind_params):
    leaving_soc_query = 'SELECT "value" FROM "leaving_soc" WHERE ("run_id" = $run_id AND "method" = $method AND "component" = $component_id AND "run_nr" = $run_nr AND "value" >= 0)'
    leaving_soc_res = client.query(leaving_soc_query, bind_params=bind_params)
    leaving_soc_df = leaving_soc_res.get('leaving_soc', None)
    return None if leaving_soc_df is None else leaving_soc_df.rename(columns={'value': 'leaving_soc'})


def separate_processes(*dfs):
    # Join all dataframes
    stats_df = dfs[0]
    for i, df in enumerate(dfs):
        if i != 0:
            stats_df = stats_df.join(df)

    # add process number
    stats_df['proc_number'] = stats_df.index
    stats_df['proc_number'] = (stats_df['proc_number'] - stats_df['proc_number'].shift())

    stats_df['proc_number'] = stats_df['proc_number'].map(lambda x: 1 if x > timedelta(minutes=1) else 0)
    stats_df['proc_number'] = stats_df['proc_number'].expanding(2).sum()
    stats_df['proc_number'] = stats_df['proc_number'].map(lambda x: 0 if np.isnan(x) else x)

    # Group by process number and add to list
    stats_df_list = [group[1].drop('proc_number', axis=1) for group in stats_df.groupby('proc_number')]
    return stats_df_list


def queue_leaving_soc_par(method, component_id, seed, run_nr):
    client = DataFrameClient(host, port, user, password, dbname)

    finish_list = []
    bind_params = {
        'run_id': run_id,
        'method': method,
        'component_id': component_id,
        'seed': seed,
        'run_nr': run_nr
    }

    leaving_soc_df = get_leaving_soc(client, bind_params)
    num_proc = 0 if leaving_soc_df is None else leaving_soc_df.size

    if num_proc > 0:
        available_df = get_available(client, bind_params)
        soc_df = get_soc(client, bind_params)
        stats_df_list = separate_processes(available_df, soc_df)
        assert (len(stats_df_list) == num_proc)

        for proc in stats_df_list:
            # drop first value as Mosaik starts with 0 anyhow
            proc = proc[1:]

            # interpolate/reduce to 100 steps
            arrival_time = proc.index[0]
            departure_time = proc.index[len(proc.index) - 1]
            sample_rate = (departure_time - arrival_time) / 100

            # detect finishTime
            finish_soc = proc['soc'].max()
            print(type(finish_soc))
            if finish_soc == 100:
                finish_time = departure_time
            else:
                finish_times = proc.loc[proc['soc'] == finish_soc]
                finish_time = finish_times.index[0]

            finish_time_percentage = (finish_time - arrival_time) / sample_rate
            assert (0 <= finish_time_percentage <= 100)

            finish_list.append({'soc': finish_soc, 'time': finish_time_percentage})
    return finish_list


def queue_data_par(method, component_id, seed, run_nr):
    client = DataFrameClient(host, port, user, password, dbname)

    proc_list = []
    bind_params = {
        'run_id': run_id,
        'method': method,
        'component_id': component_id,
        'seed': seed,
        'run_nr': run_nr
    }

    leaving_soc_df = get_leaving_soc(client, bind_params)
    num_proc = 0 if leaving_soc_df is None else leaving_soc_df.size

    if num_proc > 0:
        available_df = get_available(client, bind_params)
        soc_df = get_soc(client, bind_params)
        power_df = get_power(client, bind_params)
        stats_df_list = separate_processes(available_df, soc_df, power_df)
        assert (len(stats_df_list) == num_proc)

        for proc in stats_df_list:
            # drop first value as Mosaik starts with 0 anyhow
            proc = proc[1:]

            # interpolate/reduce to 100 steps
            arrival_time = proc.index[0]
            departure_time = proc.index[len(proc.index) - 1]
            sample_rate = (departure_time - arrival_time) / 100

            if len(proc['available']) <= 100:
                # up sampling
                proc_resample = proc.resample(sample_rate).fillna(method='nearest')
            else:
                # down sampling
                proc_resample = proc.resample(sample_rate).mean()

            # remove index and drop available column
            proc_resample = proc_resample.reset_index() \
                .drop('index', axis=1) \
                .drop('available', axis=1)
            proc_list.append(proc_resample)
    return proc_list


def query_tag(tag):
    client = DataFrameClient(host, port, user, password, dbname)
    tag_query = 'SHOW TAG VALUES WITH KEY = "' + str(tag) + '"'
    tag_res = client.query(tag_query)
    res = list(set([v['value'] for v in list(tag_res.get_points())]))
    res.sort()
    return res


def plot_soc(soc_dict, experiment):
    folder = plot_folder + 'soc/'
    if not os.path.isdir(folder):
        os.mkdir(folder)

    if len(soc_dict) == 0:
        print('No SoC Data available')
    else:
        soc_df = pd.concat(soc_dict.values(), axis=0)
        soc_df['index'] = soc_df.index
        soc_df = soc_df.sort_values('method')

        # std of soc over time
        sns.lineplot(data=soc_df, x='index', y='soc', hue='method', style='method', estimator='std', ci=None)
        plt.savefig(folder + experiment + '_soc_std' + '.png')
        plt.close()

        # mean soc over time
        sns.lineplot(data=soc_df, x='index', y='soc', hue='method', style='method', estimator='mean', ci=None)
        plt.savefig(folder + experiment + '_soc_mean' + '.png')
        plt.close()

        # QoE over time
        soc_df = soc_df.groupby(['method', 'index'], as_index=False).agg({'soc': 'std'})
        soc_df['qoe'] = 1 - (2 * soc_df['soc'] / 100)
        sns.lineplot(data=soc_df, x='index', y='qoe', hue='method', style='method', estimator='mean', ci=None)
        plt.savefig(folder + experiment + '_qoe' + '.png')
        plt.close()


def plot_power(power_dict, experiment):
    folder = plot_folder + 'power/'
    if not os.path.isdir(folder):
        os.mkdir(folder)

    if len(power_dict) == 0:
        print('No Power Data available')
    else:
        power_df = pd.concat(power_dict.values(), axis=0)
        power_df['index'] = power_df.index
        power_df = power_df.sort_values('method')

        # std of power over time
        sns.lineplot(data=power_df, x='index', y='power', hue='method', style='method', estimator='std',
                     ci=None)
        plt.savefig(folder + experiment + '_power_std' + '.png')
        plt.close()

        # mean power over time
        sns.lineplot(data=power_df, x='index', y='power', hue='method', style='method', estimator='mean',
                     ci=None)
        plt.savefig(folder + experiment + '_power_mean' + '.png')
        plt.close()


def plot_finish(finish_dict, experiment):
    folder = plot_folder + 'finish/'
    if not os.path.isdir(folder):
        os.mkdir(folder)

    if len(finish_dict) == 0:
        print('No finish Data available')
    else:
        # leaving soc vs leaving time scatter plot
        finish_df = pd.concat(finish_dict.values(), axis=0)
        finish_df = finish_df.sort_values('method')
        sns.boxenplot(data=finish_df, x='method', y='time')
        plt.savefig(folder + experiment + '_boxplot' + '.png')
        plt.close()


def main():
    folder = plot_folder
    if not os.path.isdir(folder):
        os.mkdir(folder)

    flex_evs = [t for t in query_tag('component') if 'Flex' in t]
    methods = query_tag('method')
    methods = ['SlottedAloha_participants_VDE_tau_trafo']
    # scenarios = query_tag('scenario')
    # speeds = query_tag('speed')
    # limits = query_tag('limit')
    seeds = query_tag('seed')
    seeds = ['41']
    run_nrs = query_tag('run_nr')
    run_nrs = ['2']

    #insts = [(scenario, speed, limit)
    #         for scenario in scenarios
    #         for speed in speeds
    #         for limit in limits]

    # for scenario, speed, limit in insts:
    experiment = methods[0] + '_' + run_nrs[0]
    print(experiment)
    power_dict = {}
    soc_dict = {}
    finish_dict = {}
    for method in methods:
        proc_list = []
        finish_list = []
        # collect all processes
        par_insts = [(method, comp, seed, run_nr)
                     for comp in list(flex_evs)
                     for seed in seeds
                     for run_nr in run_nrs]
        #with Pool(n_jobs) as pool:
       #     proc_list = pool.starmap(queue_data_par, par_insts)
            # finish_list = pool.starmap(queue_leaving_soc_par, par_insts)

        for value in par_insts:
            proc_list.append(queue_data_par(value[0], value[1], value[2], value[3]))
            finish_list.append(queue_leaving_soc_par(value[0], value[1], value[2], value[3]))

        proc_list = [el for sublist in proc_list for el in sublist]
        if len(proc_list) != 0:
            for i, proc in enumerate(proc_list):
                proc['proc_n'] = i

            power_df_tmp = pd.concat(proc_list, axis=0).drop('soc', axis=1)
            power_df_tmp['method'] = method
            power_dict[method] = power_df_tmp

            soc_df_tmp = pd.concat(proc_list, axis=0).drop('power', axis=1)
            soc_df_tmp['method'] = method
            soc_dict[method] = soc_df_tmp

        finish_list = [el for sublist in finish_list for el in sublist]
        if len(finish_list) != 0:
            finish_df = pd.DataFrame(finish_list)
            finish_df['method'] = method
            finish_dict[method] = finish_df

    plot_finish(finish_dict, experiment)
    plot_power(power_dict, experiment)
    plot_soc(soc_dict, experiment)


if __name__ == '__main__':
    main()
    exit()
