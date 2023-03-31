import json
import logging
import os
from datetime import date
from typing import Dict, List

import boto3
import botocore

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-release-calendar
# If an exact date is not posted yet, we use the 1st day of the month
SUPPORTED_VERSIONS = {
    # K8s minor version : (year, month, day)
    22: (2023, 6, 4),
    23: (2023, 8, 1),
    24: (2024, 1, 1),
    25: (2024, 5, 1),
}

# Notify if EOS is within this many days
EOS_WITHIN_DAYS = os.environ.get('EOS_WITHIN_DAYS', 90)
TO_EMAIL_ADDRESSES = os.environ.get('TO_EMAIL_ADDRESSES', '')
FROM_EMAIL_ADDRESS = os.environ.get('FROM_EMAIL_ADDRESS', '')
LAMBDA_ASSUME_ROLE_ARNS = os.environ.get('LAMBDA_ASSUME_ROLE_ARNS', '')
SES_TEMPLATE_NAME = os.environ.get('SES_TEMPLATE_NAME')
SES_TEMPLATE_ARN = os.environ.get('SES_TEMPLATE_ARN')

STS_CLIENT = boto3.client('sts')


def _assume_role_session(role_arn: str, role_session_name: str, **kwargs) -> boto3.Session:
    """
    Create session for use with boto3 clients using an assumed role's credentials.

    :returns: boto3 session
    """
    response = STS_CLIENT.assume_role(RoleArn=role_arn, RoleSessionName=role_session_name, **kwargs)
    credentials = response['Credentials']

    return boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )


def _paginate_clusters(eks_client: boto3.client) -> List[str]:
    paginator = eks_client.get_paginator('list_clusters')
    clusters = []

    try:
        for page in paginator.paginate():
            clusters.extend(page['clusters'])
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            pass  # Access denied due to explicit deny policy on `eks:ListClusters`
        else:
            raise error

    return clusters


def list_clusters(event: str, context: Dict) -> List[Dict]:
    logger.info(json.dumps({"[INPUT]": event}))
    region = event.get('RegionName')
    cluster_details = []

    # List clusters in the current account with Lambda role
    eks_client = boto3.client('eks', region_name=region)
    clusters = _paginate_clusters(eks_client)
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
            clusters = _paginate_clusters(eks_client)
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
    results = {"Clusters": cluster_details}
    logger.info(json.dumps({"[OUTPUT]": results}))

    return cluster_details


def version_is_supported(version: str) -> bool:
    minor = int(version.split('.')[1])
    return minor >= min(SUPPORTED_VERSIONS.keys())


def days_till_end_of_support(version: str) -> int:
    minor = int(version.split('.')[1])
    if not version_is_supported(version):
        return -1

    eos = date(*SUPPORTED_VERSIONS.get(minor))
    diff = eos - date.today()
    return diff.days


def describe_cluster(event: Dict, context: Dict) -> List[Dict]:
    """
    Describe an EKS cluster. This is singular since we are using Step Functions map state to parallelize.
    """
    logger.info(json.dumps({"[INPUT]": event}))

    lambda_assume_role_arn = event.get('lambda_assume_role_arn', None)
    region = event['region']
    cluster = event['cluster']

    eks_client = boto3.client('eks', region_name=region)
    if lambda_assume_role_arn:
        eks_session = _assume_role_session(lambda_assume_role_arn, 'EksReport-DescribeCluster')
        eks_client = eks_session.client('eks', region_name=region)

    response = eks_client.describe_cluster(name=cluster)
    logger.info(json.dumps({"[DESCRIBE CLUSTER]": response}, default=str))
    cluster = response['cluster']
    (_, _, _, region, account_id, _) = cluster['arn'].split(':')

    result = {
        'name': cluster['name'],
        'region': region,
        'account_id': account_id,
        'version': cluster['version'],
        'supported_version': version_is_supported(cluster['version']),
        'days_till_eos': days_till_end_of_support(cluster['version']),
    }

    logger.info(json.dumps({"[OUTPUT]": result}))
    return result


def sort_clusters(clusters: Dict) -> List[Dict]:
    return sorted(clusters, key=lambda x: (x['account_id'], x['region'], x['version']))


def send_email(results: Dict, email_addresses: List[str]) -> None:
    ses_client = boto3.client('sesv2')
    ses_client.send_email(
        Destination={'ToAddresses': email_addresses},
        FromEmailAddress=FROM_EMAIL_ADDRESS,
        Content={
            'Template': {
                'TemplateName': SES_TEMPLATE_NAME,
                'TemplateArn': SES_TEMPLATE_ARN,
                'TemplateData': json.dumps(
                    {
                        'eos_within_days': EOS_WITHIN_DAYS,
                        'clusters_reached_eos': results.get('reached_eos', []),
                        'clusters_near_eos': results.get('nearing_eos', []),
                    }
                ),
            }
        },
    )


def notify(event: List[Dict], context: Dict) -> None:
    logger.info(json.dumps({"[INPUT]": event}))

    # TODO - report when version of solution is not up to date (i.e. - new module published which
    # has been updated for new EKS versions and their end of support dates)
    # TODO - send to SNS topic(s)
    flattened = [item for sublist in event for item in sublist]
    logger.info(json.dumps({"[FLATTENED]": flattened}))

    # Filter and segment
    eos_clusters = filter(lambda cluster: not cluster['supported_version'], flattened)
    clusters = filter(
        lambda cluster: int(cluster.get('days_till_eos', 0)) <= int(EOS_WITHIN_DAYS) and cluster['supported_version'],
        flattened,
    )
    results = {
        'reached_eos': sort_clusters(eos_clusters),
        'nearing_eos': sort_clusters(clusters),
    }
    logger.info(json.dumps({"[OUTPUT]": results}))

    if flattened and TO_EMAIL_ADDRESSES:
        send_email(results, TO_EMAIL_ADDRESSES.split(';'))
