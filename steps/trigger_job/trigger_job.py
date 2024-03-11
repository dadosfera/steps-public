import os
import sys
import json
import logging
from contextlib import contextmanager
import requests


ORCHEST_STEP_UUID = os.environ.get("ORCHEST_STEP_UUID")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class JobIDNotFoundError(Exception):
    """Raised when the job ID is not found."""


class InvalidJobIDError(Exception):
    """Raised when the job ID is not a string."""


class TriggerJob:
    """
    Faz o trigger do target job.

    Attributes
    ----------
    logger : Logger
        Logger.
    instance_url : str
        URL do módulo de inteligência.
    target_pipeline_uuid : str
        ID da pipeline target.
    target_job_name : str
        Nome do job target.
    """

    def __init__(
        self,
        logger: logging.Logger,
        instance_url: str,
        target_pipeline_uuid: str,
        target_job_name: str,
    ):
        self.logger = logger
        self.instance_url = instance_url
        self.target_pipeline_uuid = target_pipeline_uuid
        self.target_job_name = target_job_name

    @contextmanager
    def authenticated_session(self, *args, **kwargs):
        """Gets an authenticated session by persisting the login cookie."""
        session = requests.Session(*args, **kwargs)

        try:
            ORCHEST_USER = os.environ["ORCHEST_USER"]
            ORCHEST_PASSWORD = os.environ["ORCHEST_PASSWORD"]
        except KeyError as e:
            logger.error(
                "Please provide the env_vars ORCHEST_USER and ORCHEST_PASSWORD."
            )
            raise e

        data = {
            "username": ORCHEST_USER,
            "password": ORCHEST_PASSWORD,
        }
        resp = session.post(
            f"{self.instance_url}/login", timeout=4, data=data, allow_redirects=True
        )
        if resp.status_code != 200:
            raise RuntimeError(
                "Failed to create authenticated session: Instance login failed."
            )

        try:
            yield session
        finally:
            session.close()

    def get_job_uuid(self) -> str:
        """
        Busca o id do target job.

        Returns
        ----------
        job_uuid: str
            Id do target job.
        """

        with self.authenticated_session() as session:
            response = session.get(f"{self.instance_url}/catch/api-proxy/api/jobs")

            if response.status_code != 200:
                response.raise_for_status()

            job_metadata = response.json()
            for job in job_metadata["jobs"]:
                if (
                    job["pipeline_uuid"] == self.target_pipeline_uuid
                    and job["name"] == self.target_job_name
                ):
                    job_id = job["uuid"]

                    if isinstance(job_id, str):
                        self.logger.info("Job id found!")
                        return job_id
                    else:
                        self.logger.error(
                            "Job id não encontrado. Por favor checar target_pipeline_uuid e target_job_name."
                        )
                        raise InvalidJobIDError("Job id not found.")

            self.logger.error(
                "Job id não encontrado. Por favor checar target_pipeline_uuid e target_job_name."
            )
            raise JobIDNotFoundError("Job id not found.")

    def trigger_job(self, job_uuid: str):
        """
        Faz o trigger do target job.

        Parameters
        ----------
        job_uuid: str
            Id do target job.
        """
        with self.authenticated_session() as session:
            response = session.post(
                f"{self.instance_url}/catch/api-proxy/api/jobs/{job_uuid}/runs/trigger"
            )

            if response.status_code != 200:
                response.raise_for_status()

            self.logger.info(f"{self.target_job_name} is now running!")

    def run(self):
        """Executes the process"""

        job_uuid = self.get_job_uuid()
        self.trigger_job(job_uuid)


def orchest_handler():
    import orchest

    instance_url = orchest.get_step_param("instance_url")
    target_pipeline_uuid = orchest.get_step_param("target_pipeline_uuid")
    target_job_name = orchest.get_step_param("target_job_name")

    handler = TriggerJob(
        logger=logger,
        instance_url=instance_url,
        target_pipeline_uuid=target_pipeline_uuid,
        target_job_name=target_job_name,
    )
    handler.run()


def script_handler():
    if len(sys.argv) != 2:
        raise Exception("Please provide the required configuration in JSON format")

    config_json = sys.argv[1]
    config = json.loads(config_json)

    instance_url = config["instance_url"]
    target_pipeline_uuid = config["target_pipeline_uuid"]
    target_job_name = config["target_job_name"]

    handler = TriggerJob(
        logger=logger,
        instance_url=instance_url,
        target_pipeline_uuid=target_pipeline_uuid,
        target_job_name=target_job_name,
    )
    handler.run()


if __name__ == "__main__":
    if ORCHEST_STEP_UUID is not None:
        logger.info("Running as Orchest Step")
        orchest_handler()
    else:
        logger.info("Running as script")
        script_handler()
