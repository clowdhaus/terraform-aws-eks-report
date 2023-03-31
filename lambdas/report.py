import json
import logging
import os
from typing import Dict, List

import boto3

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logger = logging.getLogger().setLevel(level=LOGLEVEL)

# Notify if EOS is within this many days
EOS_WITHIN_DAYS = os.environ.get('EOS_WITHIN_DAYS', 90)
TO_EMAIL_ADDRESSES = os.environ.get('TO_EMAIL_ADDRESSES', '')
FROM_EMAIL_ADDRESS = os.environ.get('FROM_EMAIL_ADDRESS', '')
SES_TEMPLATE_NAME = os.environ.get('SES_TEMPLATE_NAME')
SES_TEMPLATE_ARN = os.environ.get('SES_TEMPLATE_ARN')

SES_CLIENT = boto3.client('sesv2')


def _sort_clusters(clusters: List[Dict]) -> List[Dict]:
    """
    Sort clusters by account_id, region, and version for reporting purposes.

    :param clusters: list of cluster details
    :returns: sorted list of cluster details
    """
    return sorted(clusters, key=lambda x: (x['account_id'], x['region'], x['version']))


def _send_email(results: List[Dict], email_addresses: List[str]) -> None:
    """
    Send email report via SES email template

    :param results: list of cluster details to report
    :param email_addresses: list of email addresses to send report to
    :returns: None
    """
    response = SES_CLIENT.send_email(
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
    logger.info(json.dumps(response, default=str))


def notify(event: List[Dict], context: Dict) -> None:
    """
    Send EKS report notification(s)

    :param event: AWS Lambda event that contains the cluster details
    :param context: (unused) AWS Lambda context
    :returns: None
    """
    logger.info(json.dumps({'[INPUT]': event}))

    # TODO - report when version of solution is not up to date (i.e. - new module published which
    # has been updated for new EKS versions and their end of support dates)
    # TODO - send to SNS topic(s)
    flattened = [item for sublist in event for item in sublist]
    logger.info(json.dumps({'[FLATTENED]': flattened}))

    # Filter and segment
    eos_clusters = filter(lambda cluster: not cluster['supported_version'], flattened)
    clusters = filter(
        lambda cluster: int(cluster.get('days_till_eos', 0)) <= int(EOS_WITHIN_DAYS) and cluster['supported_version'],
        flattened,
    )
    results = {
        'reached_eos': _sort_clusters(eos_clusters),
        'nearing_eos': _sort_clusters(clusters),
    }
    logger.info(json.dumps({'[OUTPUT]': results}))

    if flattened and FROM_EMAIL_ADDRESS and TO_EMAIL_ADDRESSES:
        _send_email(results, TO_EMAIL_ADDRESSES.split(';'))
