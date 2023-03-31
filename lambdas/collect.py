import json
import logging
import os
from datetime import date
from typing import Dict, List

import boto3
import botocore

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logger = logging.getLogger().setLevel(level=LOGLEVEL)

# https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-release-calendar
# If an exact date is not posted yet, we use the 1st day of the month
SUPPORTED_VERSIONS = {
    # K8s minor version : (year, month, day)
    22: (2023, 6, 4),
    23: (2023, 8, 1),
    24: (2024, 1, 1),
    25: (2024, 5, 1),
}

# ARNs to assume roles across accounts to collect cluster details
LAMBDA_ASSUME_ROLE_ARNS = os.environ.get('LAMBDA_ASSUME_ROLE_ARNS', '')

STS_CLIENT = boto3.client('sts')


def _assume_role_session(role_arn: str, role_session_name: str, **kwargs) -> boto3.Session:
    """
    Create session for use with boto3 clients using an assumed role's credentials.

    :param role_arn: ARN of role to assume
    :param role_session_name: name of session used when assuming the role
    :returns: boto3 assumed role session
    """
    response = STS_CLIENT.assume_role(RoleArn=role_arn, RoleSessionName=role_session_name, **kwargs)
    credentials = response['Credentials']

    return boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )


def _paginate_clusters(eks_client: boto3.client, region: str) -> List[str]:
    """
    Paginate through all clusters in the current account (current being tied to the client).

    :param eks_client: boto3 EKS client
    :param region: AWS region; used for logging if error occurs
    :returns: list of cluster names
    """
    paginator = eks_client.get_paginator('list_clusters')
    clusters = []

    try:
        for page in paginator.paginate():
            clusters.extend(page['clusters'])
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            # TODO - add account ID to log message
            logger.warn(f'Access denied to list clusters in {region} account')
        else:
            raise error

    return clusters


def list_clusters(event: str, context: Dict) -> List[Dict]:
    """
    List clusters in the current account and across other accounts if provided.

    :param event: AWS Lambda event that contains the region name to list clusters within
    :param context: (unused) AWS Lambda context
    :returns: list of cluster details (region, cluster name, and optional assume role ARN if used)
    """
    logger.info(json.dumps({'[INPUT]': event}))
    region = event.get('RegionName')
    cluster_details = []

    # List clusters in the current account with Lambda role
    eks_client = boto3.client('eks', region_name=region)
    clusters = _paginate_clusters(eks_client, region)
    cluster_details.extend(
        map(
            lambda cluster: {
                'region': region,
                'cluster': cluster,
            },
            clusters,
        )
    )

    # List clusters in other accounts with assumed roles, if provided
    if LAMBDA_ASSUME_ROLE_ARNS:
        for lambda_assume_role_arn in LAMBDA_ASSUME_ROLE_ARNS.split(';'):
            eks_session = _assume_role_session(lambda_assume_role_arn, 'EksReport-ListClusters')
            eks_client = eks_session.client('eks', region_name=region)
            clusters = _paginate_clusters(eks_client, region)
            cluster_details.extend(
                map(
                    lambda cluster: {
                        'region': region,
                        'cluster_name': cluster,
                        'lambda_assume_role_arn': lambda_assume_role_arn,
                    },
                    clusters,
                )
            )
    results = {'Clusters': cluster_details}
    logger.info(json.dumps({'[OUTPUT]': results}))

    return cluster_details


def _version_is_supported(version: str) -> bool:
    """
    Check if the given version is supported by Amazon EKS using static list of supported versions.

    :param version: Kubernetes version to check
    :returns: True if version is supported, False otherwise
    """
    minor = int(version.split('.')[1])
    return minor >= min(SUPPORTED_VERSIONS.keys())


def _days_till_end_of_support(version: str) -> int:
    """
    Calculate the number of days until the end of support for the given version.
        If version is no longer supported, return -1

    :param version: Kubernetes version to check
    :returns: number of days until end of support, -1 if version is no longer supported
    """
    minor = int(version.split('.')[1])
    if not _version_is_supported(version):
        return -1

    eos = date(*SUPPORTED_VERSIONS.get(minor))
    diff = eos - date.today()
    return diff.days


def describe_cluster(event: Dict, context: Dict) -> List[Dict]:
    """
    Describe an EKS cluster to collect details on the cluster.
        This is singular since we are using Step Functions map state to parallelize.

    :param event: AWS Lambda event that contains the cluster name and region to describe, and optional assume role ARN
    :param context: (unused) AWS Lambda context
    :returns: list of cluster details
    """
    logger.info(json.dumps({'[INPUT]': event}))

    lambda_assume_role_arn = event.get('lambda_assume_role_arn', None)
    region = event['region']
    cluster = event['cluster']

    eks_client = boto3.client('eks', region_name=region)
    if lambda_assume_role_arn:
        eks_session = _assume_role_session(lambda_assume_role_arn, 'EksReport-DescribeCluster')
        eks_client = eks_session.client('eks', region_name=region)

    response = eks_client.describe_cluster(name=cluster)
    logger.info(json.dumps({'[DESCRIBE CLUSTER]': response}, default=str))
    cluster = response['cluster']
    (_, _, _, region, account_id, _) = cluster['arn'].split(':')

    result = {
        'name': cluster['name'],
        'region': region,
        'account_id': account_id,
        'version': cluster['version'],
        'supported_version': _version_is_supported(cluster['version']),
        'days_till_eos': _days_till_end_of_support(cluster['version']),
    }

    logger.info(json.dumps({'[OUTPUT]': result}))
    return result
