from dadosfera.services.snowflake import get_snowpark_session
import sys
import json
import logging
import os
import pandas as pd
from typing import Dict,  List, Optional

ORCHEST_STEP_UUID = os.environ.get('ORCHEST_STEP_UUID')


class StandardizeTablesInSnowflake():
    def __init__(self) -> None:
        self.orchest_step_uuid = os.environ.get('ORCHEST_STEP_UUID')
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.run()

    @staticmethod
    def get_snowflake_table(
        secret_id: str,
        table_identifier: str
    ) -> List[str]:
        session = get_snowpark_session(secret_id)
        df = session.table(table_identifier)
        return df

    def save_data_from_file(
            self,
        secret_id: str,
        table_identifier: str,
        file_path: str,
        file_format: str,
        file_format_params: Optional[Dict[str, str]] = None,
    ):
        session = get_snowpark_session(secret_id)
        session.use_schema("PUBLIC")

        self.logger.info("Creating temporary stage")
        create_temp_stage = "create or replace temporary stage my_internal_stage"
        session.sql(create_temp_stage).collect()

        self.logger.info("Putting objects into Snowflake Internal Stage")
        transformed_tbl_identifier = table_identifier.replace(
            '"', "").replace(".", "_")
        put_command = (
            f"PUT file://{file_path} @my_internal_stage/{transformed_tbl_identifier}"
        )
        session.sql(put_command).collect()

        self.logger.info("Reading Parquet File")

        if file_format == "parquet":
            result_df = session.read.parquet(
                f"@my_internal_stage/{transformed_tbl_identifier}"
            )
        elif file_format == "json":
            result_df = session.read.option("INFER_SCHEMA", "true").json(
                f"@my_internal_stage/{transformed_tbl_identifier}"
            )
        elif file_format == "csv":
            reader = session.read.option("INFER_SCHEMA", "true")

            delimiter = file_format_params.get("delimiter")
            if delimiter is not None:
                reader = reader.option("field_delimiter", delimiter)

            skip_header_option = file_format_params.get("skip_header_option")
            if skip_header_option is not None:
                reader = reader.option(
                    "skip_header_option", skip_header_option)

            result_df = reader.csv(
                f"@my_internal_stage/{transformed_tbl_identifier}")

        self.logger.info("Saving data to snowflake")
        result_df.write.mode("overwrite").save_as_table(table_identifier)

    @staticmethod
    def read_records(mapping_file_path):
        """ Lê o file JSON e retorna o conteúdo como uma lista de dicionários. """
        try:
            with open(mapping_file_path, 'r') as file:
                data = json.load(file)
                return data
        except FileNotFoundError:
            print(f"file {mapping_file_path} não encontrado.")
            return []
        except json.JSONDecodeError:
            print(f"Erro ao decodificar o file {mapping_file_path}.")
            return []

    def main(self, secret_id, mapping_file_path):

        mappeds = self.read_records(mapping_file_path)
        for mapped in mappeds:
            print(mapped)
            if not mapped["its_manual_registry"]:
                spark_df = self.get_snowflake_table(
                    secret_id, mapped["source"])
                df = spark_df.toPandas()
                df_definition = {}
                for key, item in mapped["map"].items():
                    s_name = key
                    value = item["value"]
                    value_is_column = item["is_column"]

                    if not value:
                        df_definition[s_name] = None
                    elif value_is_column:
                        df_definition[s_name] = df[value]
                    elif not value_is_column:
                        df_definition[s_name] = value

                new_df = pd.DataFrame(df_definition)

                file_path = "TEMP_JSON_LINES.json"
                new_df.to_json(file_path, orient='records', lines=True)
                schema, name = mapped["source"].split('.')
                new_table_name = f"{schema.upper()}.STANDARDIZED_{name.upper()}"
                self.save_data_from_file(secret_id=secret_id,
                                         file_path=file_path, file_format="json", table_identifier=new_table_name)

    def module_handler(self):
        import orchest
        mapping_file_path = orchest.get_step_param('mapping_file_path')
        secret_id = orchest.get_step_param('secret_id')
        output = self.main(
            mapping_file_path=mapping_file_path,
            secret_id=secret_id
        )

        orchest.output(
            data=output, name=f"{self.__class__.__name__}_output")

    def local_handler(self):
        if len(sys.argv) != 2:
            raise Exception(
                "Please provide the required configuration in JSON format")
        config_json = sys.argv[1]
        config = json.loads(config_json)

        mapping_file_path = config.get('mapping_file_path')
        secret_id = config.get('secret_id')

        output = self.main(
            mapping_file_path=mapping_file_path,
            secret_id=secret_id
        )

        with open(f"output_{self.__class__.__name__}", 'w', encoding='utf-8') as f:
            f.write(output)

    def run(self):
        """TODO Write de doc"""
        # Determina o modo de execução com base na variável de ambiente.
        if self.orchest_step_uuid is not None:
            self.logger.info('Running as an Orchest step')
            self.module_handler()
        else:
            self.logger.info('Running as standalone script')
            self.local_handler()


if __name__ == "__main__":
    StandardizeTablesInSnowflake()
