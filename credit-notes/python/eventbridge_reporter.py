
import boto3
import os
import json
from datetime import datetime, timezone


def _get_eventbridge_client():
    """Crea y retorna un cliente de EventBridge."""    
    return boto3.client(
        'events',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION')
    )


def send_event(event_details):
    """Envía un evento a Amazon EventBridge."""
    event_bus_name = os.environ.get('EVENT_BUS_NAME')
    if not event_bus_name:
        print("Advertencia: EVENT_BUS_NAME no está configurado. No se enviarán eventos.")
        return

    try:
        client = _get_eventbridge_client()
        entry = {
            'Source': 'rpa-accounting.credit-notes',
            'DetailType': 'Portal Processing Log',
            'Detail': json.dumps(event_details),
            'EventBusName': event_bus_name
        }
        
        response = client.put_events(Entries=[entry])
        
        if response['FailedEntryCount'] > 0:
            print(f"Error al enviar evento a EventBridge: {response['Entries'][0]['ErrorMessage']}")
            
    except Exception as e:
        print(f"Error al conectar con EventBridge: {e}")
