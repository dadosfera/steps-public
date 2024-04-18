import os
import json
import logging
import sys
from typing import List

from dadosfera.services.snowflake import get_snowpark_session

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_rfm_table(session, table_identifier: str, customer_id_col: str, date_col: str, monetary_col: str):
    df = session.sql(f"""WITH model AS (
                        SELECT
                            {customer_id_col} as CUSTOMER_ID,
                            MAX({date_col}) as LASTBUY,
                            DATEDIFF(DAY, MAX({date_col}), CURRENT_DATE()) AS RECENCY,
                            COUNT({customer_id_col}) AS FREQUENCY,
                            SUM({monetary_col}) AS MONETARY,
                            NTILE(5) OVER (ORDER BY SUM({monetary_col})) AS MONETARY_SCORE,
                            NTILE(5) OVER (ORDER BY COUNT({customer_id_col})) AS FREQUENCY_SCORE,
                            NTILE(5) OVER (ORDER BY DATEDIFF(DAY, MAX({date_col}), CURRENT_DATE()) DESC) AS RECENCY_SCORE,
                            (FREQUENCY_SCORE + MONETARY_SCORE) / 2 as mean_monetary_frequency,
                            CASE 
                                WHEN RECENCY_SCORE = 5 THEN
                                    CASE
                                        WHEN mean_monetary_frequency < 2 THEN 'New Customers'
                                        WHEN mean_monetary_frequency < 3 THEN 'Potential Loyalist'
                                        WHEN mean_monetary_frequency <= 5 THEN 'Champions'
                                    END
                                WHEN RECENCY_SCORE = 4 THEN
                                    CASE
                                        WHEN mean_monetary_frequency = 1 THEN 'Promising'
                                        WHEN mean_monetary_frequency < 3 THEN 'Potential Loyalist'
                                        WHEN mean_monetary_frequency <= 5 THEN 'Loyal Customer'
                                    END
                                WHEN RECENCY_SCORE = 3 THEN
                                    CASE
                                        WHEN mean_monetary_frequency <= 2 THEN 'Needs Attention'
                                        WHEN mean_monetary_frequency = 3 THEN 'About to Sleep'
                                        WHEN mean_monetary_frequency <= 5 THEN 'Loyal Customer'
                                    END
                                WHEN RECENCY_SCORE <= 2 THEN
                                    CASE
                                        WHEN mean_monetary_frequency <= 2 THEN 'Hibernating'
                                        WHEN mean_monetary_frequency <= 4 THEN 'At Risk'
                                        WHEN mean_monetary_frequency <= 5 THEN 'Cannot Lose Them'
                                    END
                                ELSE 'Categoria não encontrada'
                            END AS CUSTOMER_TYPE
                        FROM {table_identifier}
                        WHERE {date_col} >= LAST_DAY({date_col}) - INTERVAL '1 YEAR'
                        GROUP BY ALL
                    ),
                    last_transactions AS (
                        SELECT 
                            CUSTOMER_ID,
                            AMOUNT_LAST_40D,
                            TOTAL_MONETARY_40D,
                            MEAN_MONETARY_40D,
                            STD_MONETARY_40D
                        FROM (
                            SELECT 
                                {customer_id_col} as CUSTOMER_ID,
                                FIRST_VALUE({monetary_col}) OVER (PARTITION BY {customer_id_col} ORDER BY {date_col} DESC) as AMOUNT_LAST_40D,
                                SUM({monetary_col}) OVER (PARTITION BY {customer_id_col}) as TOTAL_MONETARY_40D,
                                AVG({monetary_col}) OVER (PARTITION BY {customer_id_col}) as MEAN_MONETARY_40D,
                                STDDEV_POP({monetary_col}) OVER (PARTITION BY {customer_id_col}) as STD_MONETARY_40D,
                                ROW_NUMBER() OVER (PARTITION BY {customer_id_col} ORDER BY {date_col} DESC) as rn
                            FROM {table_identifier}
                            WHERE {date_col} >= LAST_DAY({date_col}) - INTERVAL '40 DAY'
                        ) AS LAST_40D_PURCHASES
                        WHERE rn = 1
                    )

                    SELECT model.*,
                          last_transactions.* EXCLUDE (CUSTOMER_ID)
                    FROM model
                    LEFT JOIN last_transactions ON model.CUSTOMER_ID=last_transactions.CUSTOMER_ID""").collect()
    return df.queries

def orchest_handler():
    import orchest

    secret_id = orchest.get_step_param('secret_id')
    table_identifier = orchest.get_step_param('table_identifier')
    customer_id_col = orchest.get_step_param('customer_id_col')
    date_col = orchest.get_step_param('date_col')
    monetary_col = orchest.get_step_param('monetary_col')

    session = get_snowpark_session(secret_id)
    queries = create_rfm_table(session, table_identifier, customer_id_col, date_col, monetary_col)

    output_type = orchest.get_step_param('output_type')
    if output_type == 'to_filepath':
        output_filepath = orchest.get_step_param('output_filepath')
        with open(output_filepath, 'w') as f:
            f.write(json.dumps(queries))
    elif output_type == 'to_outgoing_variable':
        output_variable_name = orchest.get_step_param('output_variable_name')
        orchest.output(data=queries, name=output_variable_name)


def script_handler(config: dict):
    secret_id = config.get('secret_id')
    table_identifier = config.get('table_identifier')
    customer_id_col = config.get('customer_id_col')
    date_col = config.get('date_col')
    monetary_col = config.get('monetary_col')
    output_filepath = config.get('output_filepath')

    session = get_snowpark_session(secret_id)
    queries = create_rfm_table(session, table_identifier, customer_id_col, date_col, monetary_col)

    with open(output_filepath, 'w') as f:
        f.write(json.dumps(queries))


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        if len(sys.argv) != 2:
            raise Exception("Please provide the required configuration in JSON format")
        config_json = sys.argv[1]
        config = json.loads(config_json)
        script_handler(config)