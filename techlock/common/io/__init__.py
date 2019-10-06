import pkg_resources
from urllib.parse import urlparse
from ..util.aws import get_client


def default_reader(stream):
    return stream.read()


def read_file(file_url, reader=default_reader, **reader_kw_args):
    '''
        Reads a file using the provided reader.

        Example:
            read_file('/home/user/test.txt')
            read_file('s3://my_bucket/key/to/file.json', json.load)
            read_file('py://my_module/file.csv', csv.reader)
    '''
    url = urlparse(file_url)

    if url.scheme == 's3':
        s3_client = get_client('s3')
        s3_object = s3_client.get_object(
            Bucket=url.hostname,
            Key=url.path.strip('/')
        )
        return reader(s3_object['Body'], **reader_kw_args)
    elif url.scheme == 'py':
        # Read from python module
        return reader(pkg_resources.resource_stream(url.netloc, url.path.lstrip('/')), **reader_kw_args)
    elif url.scheme in ('file', ''):
        # Read from local path
        with open(url.path) as fin:
            return reader(fin, **reader_kw_args)
    else:
        raise NotImplementedError('"{}" is not implemented. Please use one of ("s3", "py", "file")'.format(url.scheme))
