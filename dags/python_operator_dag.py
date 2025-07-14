from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def my_function():
    print("Hello from my_function")

with DAG(
    dag_id='my_python_function_dag',
    start_date=datetime(2025,7,12),
    schedule='@daily',
    catchup=False
) as dag:
    
    run_my_function = PythonOperator(
        task_id = 'run_my_function',
        python_callable = my_function
    )

    run_my_function