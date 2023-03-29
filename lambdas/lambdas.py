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

STS_CLIENT = boto3.client('sts')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <title>EKS Report</title>
  <style>
    body {
        font-family: arial, sans-serif;
        font-size: 0.9em;
    }
    table, th, td {
      border: 1px solid black;
      border-collapse: collapse;
    }
    th, td {
      padding: 0.5em;
    }
    th {
      text-align: left;
    }
  </style>
</head>
<body>
  <main>
    <h1>EKS Report</h1>
    {{reached_eos_clusters}}{{nearing_eos_clusters}}{{no_clusters}}

    <p>This report was generated using the <a href="https://github.com/clowdhaus/terraform-aws-eks-report">terraform-aws-eks-report</a> project.</p>
  </main>
</body>
</html>
"""


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
            pass # Access deined due to explicit deny policy on `eks:ListClusters`
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
    newline = '\n'

    clusters_reached_eos = results.get('reached_eos', [])
    if clusters_reached_eos:
        reached_eos_data = []
        for cluster in clusters_reached_eos:
            reached_eos_data.append(
                f"""
            <tr>
                <td>{cluster['name']}</td>
                <td>{cluster['account_id']}</td>
                <td>{cluster['region']}</td>
                <td>{cluster['version']}</td>
            </tr>"""
            )

        reached_eos_clusters = f"""
        <h2>Clusters w/ Unsupported Version</h2>

        <table>
            <tr>
                <th>Cluster Name</th>
                <th>Account ID</th>
                <th>Region</th>
                <th>Version</th>
            </tr>
            {newline.join(reached_eos_data)}
        </table>\n"""
    else:
        reached_eos_clusters = ''

    clusters_near_eos = results.get('nearing_eos', [])
    if clusters_near_eos:
        nearing_eos_data = []
        for cluster in clusters_near_eos:
            nearing_eos_data.append(
                f"""
            <tr>
                <td>{cluster['name']}</td>
                <td>{cluster['account_id']}</td>
                <td>{cluster['region']}</td>
                <td>{cluster['version']}</td>
                <td>{cluster['days_till_eos']}</td>
            </tr>"""
            )

        nearing_eos_clusters = f"""
        <h2>Clusters w/ Version Nearing End of Support</h2>

        <table>
            <tr>
                <th>Cluster Name</th>
                <th>Account ID</th>
                <th>Region</th>
                <th>Version</th>
                <th>Days Until EOS</th>
            </tr>
            {newline.join(nearing_eos_data)}
        </table>\n"""
    else:
        nearing_eos_clusters = ''

    results = HTML_TEMPLATE.replace('{{reached_eos_clusters}}', reached_eos_clusters)
    results = results.replace('{{nearing_eos_clusters}}', nearing_eos_clusters)
    if not reached_eos_clusters and not nearing_eos_clusters:
        results = results.replace(
            '{{no_clusters}}',
            f'<p>No clusters found with unsupported versions or with versions that will reach end of support within the next {EOS_WITHIN_DAYS} days.</p>',
        )
    else:
        results = results.replace('{{no_clusters}}', '')

    ses_client.send_email(
        Destination={'ToAddresses': email_addresses},
        Content={
            'Simple': {
                'Subject': {
                    'Data': 'EKS Report',
                },
                'Body': {
                    'Html': {
                        'Data': results,
                    }
                },
            },
        },
        FromEmailAddress=FROM_EMAIL_ADDRESS,
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
        lambda cluster: int(cluster.get('days_till_eos', 0)) <= int(EOS_WITHIN_DAYS) and cluster['supported_version'], flattened
    )
    results = {
        'reached_eos': sort_clusters(eos_clusters),
        'nearing_eos': sort_clusters(clusters),
    }
    logger.info(json.dumps({"[OUTPUT]": results}))

    if flattened and TO_EMAIL_ADDRESSES:
        send_email(results, TO_EMAIL_ADDRESSES.split(';'))
