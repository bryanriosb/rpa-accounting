import uuid
import boto3
import os
from datetime import datetime, timedelta, timezone


def _get_dynamodb_resource():
    """Crea y retorna un recurso de DynamoDB."""
    aws_region = os.environ.get('AWS_REGION')
    if not aws_region:
        raise ValueError("La variable de entorno AWS_REGION no está configurada.")
    
    return boto3.resource(
        'dynamodb',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=aws_region
    )


def save_item_to_dynamodb(item, table_name):
    """Guarda un item genérico en una tabla de DynamoDB."""
    try:
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(table_name)
        table.put_item(Item=item)
        print(f"Successfully saved item to {table_name}.")
    except Exception as e:
        print(f"Error saving item to {table_name}: {e}")


def save_portal_report(report_data):
    """Prepara y guarda el reporte de un portal en DynamoDB."""
    bogota_tz = timezone(timedelta(hours=-5))
    execution_timestamp = datetime.now(bogota_tz).strftime('%Y-%m-%d %H:%M:%S')

    item = {
        'id': uuid.uuid4().hex,
        'portalName': report_data.get('portal_name'),
        'createdAt': execution_timestamp,
        'url': report_data.get('url'),
        'status': report_data.get('status'),
        'pdfsDownloaded': report_data.get('pdfs_downloaded'),
        'errors': report_data.get('errors'),
        'files': report_data.get('files'),
        'targetDate': report_data.get('target_date'),
    }

    item = {k: v for k, v in item.items() if v is not None}
    table_name = os.environ.get('DYNAMODB_TABLE', 'PortalReports')
    save_item_to_dynamodb(item, table_name)


def save_global_summary(summary_data):
    """Prepara y guarda el resumen global en DynamoDB."""
    bogota_tz = timezone(timedelta(hours=-5))
    execution_timestamp = datetime.now(bogota_tz).strftime('%Y-%m-%d %H:%M:%S')

    item = {
        'id': uuid.uuid4().hex,
        'createdAt': execution_timestamp,
        'totalPortalsProcessed': summary_data.get('total_portals_processed'),
        'successfulPortals': summary_data.get('successful_portals'),
        'partialPortals': summary_data.get('partial_portals'),
        'failedPortals': summary_data.get('failed_portals'),
        'totalPdfsDownloaded': summary_data.get('total_pdfs_downloaded'),
        'totalErrors': summary_data.get('total_errors'),
    }

    item = {k: v for k, v in item.items() if v is not None}
    table_name = os.environ.get('DYNAMODB_SUMMARY_TABLE', 'ExecutionSummaries')
    save_item_to_dynamodb(item, table_name)