from pydantic import ValidationError
from app.integrations.site_client import SiteClient
from app.schemas.integration.shipments import ShipmentRecordIngestion, ShipmentsIngestionResponse

class ShipmentSyncService:
    def __init__(self):
        self.site_client = SiteClient()

    def sync_shipments(self) -> ShipmentsIngestionResponse:
        try:
            raw_shipments = self.site_client.get_shipments()
        

            valid_shipments = []
            for raw_shipment in raw_shipments:
                try: 
                    shipment = ShipmentRecordIngestion.model_validate(raw_shipment)
                    valid_shipments.append(shipment)
                except ValidationError as e:
                    print(f"Validation error for shipment {raw_shipment['shipment_id']}: {e}")
                    continue

            return ShipmentsIngestionResponse(status='ok', shipments=valid_shipments)   
        except Exception as e:
            raise ValueError(f"Error syncing shipments: {e}")