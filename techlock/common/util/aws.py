import logging
from dataclasses import dataclass
from urllib.parse import urlparse, ParseResult
from typing import Union

import boto3
import requests
from techlock.common.config import ConfigManager

logger = logging.getLogger("aws-util")


@dataclass
class AWSConfig:
    access_key: str = None
    secret_key: str = None
    session_token: str = None
    region_name: str = None


@dataclass
class S3Object:
    bucket: str
    key: str

    @staticmethod
    def from_url(url: Union[str, ParseResult]):
        if isinstance(url, str):
            url = urlparse(url)
        if url.scheme != 's3':
            raise ValueError('URL scheme must be S3.')

        return S3Object(url.hostname, url.path.lstrip('/'))

    def exists(self):
        try:
            self.get_object()
            return True
        except:  # noqa
            return False

    def get_object(self):
        s3 = get_client('s3')
        return s3.get_object(
            Bucket=self.bucket,
            Key=self.key
        )

    def get_line_iter(self, chunk_size=128_000):
        s3_obj = self.get_object()
        return s3_obj['Body'].iter_lines(chunk_size=chunk_size)


def get_aws_configuration(tenant_id: str = None):
    custom_config = {
        "AWS_ACCESS_KEY_ID": ConfigManager().get(tenant_id, "AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": ConfigManager().get(tenant_id, "AWS_SECRET_ACCESS_KEY"),
        "AWS_SESSION_TOKEN": ConfigManager().get(tenant_id, "AWS_SESSION_TOKEN"),
        "AWS_DEFAULT_REGION": ConfigManager().get(tenant_id, "AWS_DEFAULT_REGION")
    }

    if not custom_config.get("AWS_SECRET_ACCESS_KEY") or not custom_config.get("AWS_ACCESS_KEY_ID"):
        session = boto3.session.Session()
        credentials = session.get_credentials()
        if not credentials.access_key or not credentials.secret_key or not session.region_name:
            logger.debug("AWS config not found.")

        if session.region_name:
            region_name = session.region_name
        else:
            try:
                response = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document', timeout=3)
                region_name = response.json().get('region')
            except Exception as e:
                logger.debug('Could not get EC2 instance-identity document: %s', e)

        return AWSConfig(
            access_key=credentials.access_key if credentials.access_key is None else str(credentials.access_key),
            secret_key=credentials.secret_key if credentials.secret_key is None else str(credentials.secret_key),
            session_token=credentials.token if credentials.token is None else str(credentials.token),
            region_name=region_name or 'us-east-1'
        )

    return AWSConfig(
        access_key=custom_config.get("AWS_ACCESS_KEY_ID"),
        secret_key=custom_config.get("AWS_SECRET_ACCESS_KEY"),
        session_token=custom_config.get("AWS_SESSION_TOKEN"),
        region_name=custom_config.get("AWS_DEFAULT_REGION")
    )


def get_client(name):
    aws_config = get_aws_configuration()
    kwargs = {
        'aws_secret_access_key': aws_config.secret_key,
        'aws_access_key_id': aws_config.access_key,
        'aws_session_token': aws_config.session_token,
        'region_name': aws_config.region_name
    }

    endpoint = ConfigManager().get(None, "{}_ENDPOINT_URL".format(name.upper().replace('-', '_')))
    if endpoint:
        kwargs['endpoint_url'] = endpoint

    return boto3.client(
        name,
        **kwargs
    )


def get_session():
    aws_config = get_aws_configuration()
    return boto3.session.Session(
        aws_secret_access_key=aws_config.secret_key,
        aws_access_key_id=aws_config.access_key,
        aws_session_token=aws_config.session_token,
        region_name=aws_config.region_name
    )
