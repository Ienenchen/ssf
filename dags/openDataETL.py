import csv
from textwrap import dedent
import pandas as pd
import numpy as np
import pendulum
from airflow import DAG
import os

from airflow.operators.python import PythonOperator
from airflow.operators.dummy_operator import DummyOperator

with DAG(
    'openDataETL',
    default_args={'retries': 2},
    description='ETL DAG For OpenData - House Price',
    schedule_interval=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=['ssf'],
) as dag:
    # [START extract_function]
    def extract(**kwargs):
        seasons = ['109S1', '109S2', '109S3', '109S4',
                   '110S1', '110S2', '110S3', '110S4', '111S1']
        filenames = ['A_LVR_LAND_A', 'F_LVR_LAND_A',
                     'E_LVR_LAND_A', 'H_LVR_LAND_B', 'B_LVR_LAND_B']
        df_all = pd.DataFrame()
        for season in seasons:
            for file in filenames:
                url = 'https://plvr.land.moi.gov.tw//DownloadSeason?season={}&fileName={}.csv'.format(
                    season, file)
                df = pd.read_csv(
                    url, header=1, quoting=csv.QUOTE_NONE, encoding='utf-8')
                df['df_name'] = season.replace(
                    'S', '_')+'_'+file.replace('LVR_LAND_', '')
                df_all = pd.concat([df_all, df])
        df_all.to_csv('/opt/airflow/logs/df_all.csv', index=False)

    # [END extract_function]

    # [START transform_function]
    def transform_filter1():
        df_all = pd.read_csv('/opt/airflow/logs/df_all.csv')
        df_1 = df_all.loc[df_all['the use zoning or compiles and checks'] == '商']
        df_1.to_csv('/opt/airflow/logs/results/df1_filter.csv', index=False)

    def transform_filter2():
        df_all = pd.read_csv('/opt/airflow/logs/df_all.csv')
        df_2 = df_all.loc[df_all['building state'].str.contains(
            '住宅大樓', regex=False)]
        df_2.to_csv('/opt/airflow/logs/results/df2_filter.csv', index=False)

    def transform_filter3():
        df_all = pd.read_csv('/opt/airflow/logs/df_all.csv')
        all_number = ['十四層', '十三層', '十五層', '十九層', '十八層', '十六層', '二十一層', '二十三層', '十七層', '三十層', '二十九層', '二十六層', '二十五層', '二十層', '二十二層', '二十四層', '三十一層', '三十八層', '四十二層', '二十七層', '二十八層', '三十三層', '三十七層', '三十二層', '三十六層', '三十四層', '四十六層', '四十一層', '四十三層', '四十層', '三十五層', '三十九層', '八十五層', '五十層', '15', '13', '30', '14', '22', '26', '27', '25', '17', '六十八層', '21', '24', '19', '18', '28', '29',
                      '20', '15.0', '14.0', '13.0', '23.0', '29.0', '12.0', '35.0', '19.0', '26.0', '16.0', '17.0', '28.0', '20.0', '18.0', '24.0', '25.0', '22.0', '21.0', '39.0', '68.0', '27.0', '38.0', '37.0', '41.0', '85.0', '33.0', '50.0', '36.0', '16', '23', '31', '36', '33', 13, 15, 24, 14, 25, 19, 17, 28, 31, 29, 21, 16, 26, 18, 27, 22, 23, 20, 34, 36, 33, 35, 32, '34', '35', '32']
        df_3 = df_all.loc[df_all['total floor number'].isin(all_number)]
        df_3.to_csv('/opt/airflow/logs/results/df3_filter.csv', index=False)

    def transform_count4():
        df_all = pd.read_csv('/opt/airflow/logs/df_all.csv')
        rowcounts = len(df_all.index)
        dataList = df_all['transaction pen number'].str.split(
            pat='車位').tolist()
        df_all[['splitPart1', 'parkingLotNumber']] = dataList

        rowcounts = len(df_all.index)
        totalParkingLotNumber = df_all['parkingLotNumber'].astype(
            np.int64).sum()
        avgTotalPrice = df_all['total price NTD'].mean()
        avgBerthPrice = df_all['the berth total price NTD'].mean()
        data = [[rowcounts, totalParkingLotNumber, avgTotalPrice, avgBerthPrice]]
        df = pd.DataFrame(data, columns=['總件數', '總車位數', '平均總價元', '平均車位總價元'])
        df.to_csv('/opt/airflow/logs/results/df_count.csv', index=False)

    # [END transform_function]

    # [END load_function]

    # [START main_flow]
    extract_task = PythonOperator(
        task_id='extract',
        python_callable=extract,
    )

    start_task = DummyOperator(
        task_id='start'
    )

    transform_task_1 = PythonOperator(
        task_id='transform1',
        python_callable=transform_filter1,
    )

    transform_task_2 = PythonOperator(
        task_id='transform2',
        python_callable=transform_filter2,
    )

    transform_task_3 = PythonOperator(
        task_id='transform3',
        python_callable=transform_filter3,
    )

    transform_task_4 = PythonOperator(
        task_id='transform4',
        python_callable=transform_count4,
    )
    end_task = DummyOperator(
        task_id='end'
    )
    extract_task >> start_task
    start_task >> transform_task_1 >> end_task
    start_task >> transform_task_2 >> end_task
    start_task >> transform_task_3 >> end_task
    start_task >> transform_task_4 >> end_task
    # transform_task >> load_task

# [END main_flow]
