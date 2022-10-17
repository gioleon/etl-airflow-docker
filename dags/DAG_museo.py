import os
from tempfile import TemporaryDirectory
import pandas as pd
from urllib.error import HTTPError
from pathlib import Path
from datetime import datetime
from airflow import DAG
from decouple import config
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook


def get_data():
    """
    This function will execute some
    functions and conditions to determinate
    if there is new data to insert or not.
    """
    import requests

    # Root
    root_folder = Path(__file__).parent.parent

    # Get data
    response = requests.get('https://datos.cultura.gob.ar/dataset/37305de4-3cce-4d4b-9d9a-fec3ca61d09f/resource/4207def0-2ff7-41d5-9095-d42ae8207a5d/download/museos_datosabiertos.csv')

    # If not exists, create folder
    if not os.path.exists(Path(root_folder, 'files/museos')):
        os.makedirs(Path(root_folder, 'files/museos'))

    try:
        if response.ok:
            with open(Path(
                root_folder,
                'files/museos/new_museos_data.csv'
            ), 'wb') as f:
                f.write(response.content)
    except HTTPError as http_error:
        print(http_error)
    except Exception as ex:
        print(ex)

    new_df = pd.read_csv(Path(
        root_folder,
        'files/museos/new_museos_data.csv'
    ))

    # Check if there is existing data
    if not os.path.exists(Path(
        root_folder, 'datasets/museos/previous_museos_data.csv'
    )):
        # Create folder if it doesn't exists
        if not os.path.exists(Path(root_folder, 'datasets/museos')):
            os.makedirs(Path(root_folder, 'datasets/museos'))

        # Save into datasets folder.
        new_df.to_csv(
            Path(
                root_folder,
                'datasets/museos/last_museos_data.csv'),
            index=False
        )
    else:
        # Read files.
        last_df = pd.read_csv(Path(
            root_folder, 'datasets/museos/last_museos_data.csv'
        ))

        # Check if exists new data
        previous_data_length = last_df.shape[0]
        new_data_length = new_df.shape[0]

        if new_data_length > previous_data_length:
            # Concat files in a temporary dataframe
            temp_merged = pd.concat([new_df, last_df])

            # Drop duplicates in the temporary dataframe
            temp_merged = temp_merged.drop_duplicates(
                keep=False).reset_index(drop=True)

            # Save temporary dataframe
            temp_merged.to_csv(Path(
                root_folder, 'datasets/museos/temp_museos_data.csv'
            ))
        else:
            raise 'There is no new data to add.'


def get_cols_insterest(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    This function takes a dataframe and returns a
    new dataframe with just columns of interest.

    @input: dataframe(pandas.DataFrame)

    @output: pandas.DataFrame
    """

    # Cols to rename
    col_names = {'cod_loc': 'localidad_id', 'idprovincia': 'provincia_id', 'iddepartamento': 'departamento_id', 'tipolatitudlongitud': 'tipo_latitud_longitud', 'jurisdiccion': 'tipo_de_gestion'}

    # Columns of interest
    cols = ['nombre', 'telefono', 'mail', 'categoria', 'direccion', 'departamento_id', 'provincia', 'provincia_id', 'localidad', 'localidad_id', 'latitud', 'longitud', 'tipo_latitud_longitud', 'año_inauguracion', 'actualizacion', 'tipo_de_gestion']

    # Column names to lower case
    dataframe = dataframe.rename(str.lower, axis=1)

    # Rename columns based on col_names
    dataframe = dataframe.rename(col_names, axis=1)

    return dataframe[cols]


def clean_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    This function takes the given data frame 
    and applies a process to clean the columns 
    based on the exploratory data analysis
    previously done.

    @input: dataframe(pandas.DataFrame)

    @output: pandas.DataFrame
    """
    import unidecode
    import numpy as np 

    # NORMALIZE DATA
    str_cols = ['nombre', 'categoria', 'provincia', 'localidad', 'tipo_latitud_longitud', 'tipo_de_gestion', 'tipo_de_gestion', 'direccion']

    # String columns to lower case.
    for col in str_cols:
        dataframe[col] = list(map(
            lambda x: x 
            if type(x) == float
            else
            str.lower(x),
            dataframe[col].values
        ))

    # Replacing stress vowels
    for col in str_cols:
        dataframe[col] = list(map(
            lambda x: 
            unidecode.unidecode(x)
            if type(x) != float
            else
            x,
            dataframe[col].values
        ))

    # Treating missing values in the cols of interest
    """
    Giving a look at the columns i realized 
    that there are some missing values (nan) present there; 
    however, there are some words that also represent
    missing values (sin direccion, s/n), so, let's unify them. 
    """
    for col in dataframe.select_dtypes(['string', 'object']).columns:
        dataframe[col] = list(map(
            lambda x:
            np.nan
            if x in ['sin direccion', 's/d', 's/n', 'nan', 'notiene', '\n']
            else x,
            dataframe[col].values
        ))
    
    # Transform phone number
    if 'telefono' in dataframe.columns:
        dataframe["telefono"] = dataframe["telefono"].apply(
            lambda x: x
            if type(x) == float
            else
            x.replace(',', '').replace(' ', '')
        )

        dataframe['telefono'] = dataframe['telefono'].apply(
            lambda x: x
            if len(str(x)) >= 6
            else
            np.nan
        )

    # Transform año_inaguracion
    if 'año_inauguracion' in dataframe.columns:
        dataframe['año_inauguracion'] = list(map(
            lambda x: x
            if x != 0
            else
            np.nan
        ))

    # Impute missing values in actualizacion
    dataframe['actualizacion'] = list(map(
        lambda x: x
        if len(str(x)) == 4
        else
        np.nan,
        dataframe['actualizacion'].values
    ))

    # Change data types.
    dataframe[["categoria", "provincia", "localidad"]] = dataframe[[
        "categoria",
        "provincia",
        "localidad"
    ]].astype("category")

    dataframe[['nombre', 'localidad_id', "provincia_id", "departamento_id", 'tipo_de_gestion']] = dataframe[[
        'nombre', "localidad_id", "provincia_id", "departamento_id", 'tipo_de_gestion'
    ]].astype("string")

    # Set the date where data was upload.
    dataframe["fecha_carga"] = datetime.now()

    return dataframe


def transform_data():
    """
    This function takes de recently downloaded data
    and impute missing values, normalize data, treat string, etc.
    """

    import numpy as np
    import unidecode

    # Root
    root_folder = Path(__file__).parent.parent

    if not os.path.exists(Path(
        root_folder, 'datasets/museos/previous_museos_data.csv'
    )):
        # Read csv to clean
        last = pd.read_csv('files/museos/new_museos_data.csv')

        # Get and clean just columns of interest
        last = get_cols_insterest(last)

        # Clean columns
        last = clean_columns(last)

        # Save
        last.to_csv(
            'datasets/museos/previous_museos_data.csv',
            index=False
        )

    else:
        if os.path.exists(Path(
            root_folder, 'datasets/museos/temp_museos_data.csv'
        )):
            # Load temp file and cleaned file
            temp_df = pd.read_csv(
                'datasets/museos/temp_museos_data.csv')
            clean_df = pd.read_csv(
                'datasets/museos/previous_museos_data.csv')

            # Get columns of interest and rename columns
            temp_df = get_cols_insterest(temp_df)

            # Clean temp 
            temp_df = clean_columns(temp_df)

            # merge it to the main file.
            final_df = pd.concat(
                [clean_df, temp_df],
                ignore_index=True
            )

            # Save file
            final_df.to_csv(
                'datasets/museos/previous_museos_data.csv',
                index=False
            )

            # Delete temporal data
            os.remove('datasets/museos/temp_museos_data.csv')


def load_data():
    import boto3

    client = boto3.client(
        's3', aws_access_key_id=config('ACCESS_KEY_ID'),
        aws_secret_access_key=config('SECRET_ACCESS_KEY'),
        region_name=config('REGION')
    )

    client.upload_file(
        r'datasets/museos/previous_museos_data.csv',
        config('BUCKET_NAME'),
        r'datasets/museos/previous_museos_data.csv'
    )


with DAG(
    dag_id='DAG_museo',
    description='ETL new data of cines',
    default_args={},
    start_date=datetime(2022, 10, 11),
    schedule_interval='@monthly',
    catchup=False
) as dag:

    task_get_data = PythonOperator(
        task_id='get_data',
        python_callable=get_data
    )

    task_transform_data = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data
    )

    task_load_data = PythonOperator(
        task_id='load_data',
        python_callable=load_data
    )

    # Flow.
    task_get_data >> task_transform_data >> task_load_data