from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator



with DAG(
    dag_id='my_bash_operator_dag',
    start_date=datetime(2025,7,12),
    schedule='@daily',
    catchup=False
) as dag:
    
    run_my_function = BashOperator(
        task_id = 'run_bash_operator',
        bash_command = "echo Hello from bash"
    )

    run_my_function