from datetime import datetime, date
from pydantic import BaseModel, Field, model_validator
from typing import Self

class ShipmentRecordIngestion(BaseModel):
    shipment_id: str = Field(min_length=1, max_length=50)
    site_id: str = Field(min_length=1, max_length=50)
    part_id: str = Field(min_length=1, max_length=50)
    ship_date: date
    expected_delivery_date: date
    actual_delivery_date: date | None
    quantity_shipped: int = Field(gt=0)
    shipment_status: str = Field(min_length=1, max_length=50)
    delayed_flag: bool
    delay_days: int = Field(ge=0)
    supplier_id: str = Field(min_length=1, max_length=50)
    supplier_name: str = Field(min_length=1, max_length=100)
    updated_at: datetime

    @model_validator(mode='after')
    def validate_dates(self) -> Self:
        if self.expected_delivery_date < self.ship_date:
            raise ValueError('Expected delivery date must be on or after ship date')

        if self.actual_delivery_date is None:
            if self.delayed_flag:
                raise ValueError(
                    'delayed_flag must be False when actual delivery date is missing'
                )
            if self.delay_days != 0:
                raise ValueError(
                    'delay_days must be 0 when actual delivery date is missing'
                )
            return self

        if self.actual_delivery_date < self.ship_date:
            raise ValueError('Actual delivery date must be on or after ship date')

        expected_delay_days = max(
            (self.actual_delivery_date - self.expected_delivery_date).days,
            0,
        )
        if self.delay_days != expected_delay_days:
            raise ValueError(
                'delay_days must equal max(actual_delivery_date - expected_delivery_date, 0) in days'
            )

        if (
            self.actual_delivery_date <= self.expected_delivery_date
            and self.delayed_flag
        ):
            raise ValueError(
                'delayed_flag must be False when delivery is on or before the expected date'
            )

        if (
            self.actual_delivery_date > self.expected_delivery_date
            and not self.delayed_flag
        ):
            raise ValueError(
                'delayed_flag must be True when delivery is after the expected date'
            )

        return self


class ShipmentsIngestionResponse(BaseModel):
    status: str
    shipments: list[ShipmentRecordIngestion]
