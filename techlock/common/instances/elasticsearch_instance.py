import logging
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from dataclasses import dataclass
from elasticsearch import Elasticsearch, RequestsHttpConnection

from .instance import ClosableInstance
from ..config import ConfigManager
from ..util.aws import get_session
from ..util.helper import parse_boolean

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ElasticSearchConfig:
    host: str
    port: int
    use_ssl: bool
    aws_hosted: bool

    @staticmethod
    def get(tenant_id: str, instance_name: str = None) -> 'ElasticSearchConfig':
        key = 'elasticsearch'
        if instance_name is not None:
            key += '.' + instance_name

        cm = ConfigManager()
        es_config = ElasticSearchConfig(
            host=cm.get(tenant_id, key + '.host'),
            port=int(cm.get(tenant_id, key + '.port', 9200)),
            use_ssl=parse_boolean(cm.get(tenant_id, key + '.use_ssl', False)),
            aws_hosted=parse_boolean(cm.get(tenant_id, key + '.aws_hosted', False))
        )
        return es_config


class ElasticSearchInstance(ClosableInstance):
    def __init__(
        self,
        tenant_id: str = ConfigManager._DEFAULT_TENANT_ID,
        instance_name: str = None
    ):
        self.tenant_id = tenant_id
        self.config = ElasticSearchConfig.get(tenant_id, instance_name)
        self.instance = None

    def get(self):
        logger.debug('Initializing ES with config %s', self.config)
        awsauth = None
        if self.config.aws_hosted:
            logger.info('ES is AWS Hosted')
            # We need to sign the ES requests: https://github.com/boto/boto3/issues/853
            session = get_session()
            awsauth = BotoAWSRequestsAuth(
                aws_host=self.config.host,
                aws_region=session.region_name,
                aws_service='es'
            )

        self.instance = Elasticsearch(
            hosts=[{'host': self.config.host, 'port': self.config.port}],
            http_auth=awsauth,
            use_ssl=self.config.use_ssl,
            verify_certs=self.config.port == 443,
            connection_class=RequestsHttpConnection
        )

        return self.instance

    def close(self):
        return True
