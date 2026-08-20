import { parseDate, type CalendarDate } from '@internationalized/date'
import { useState } from 'react'
import { DateRangePickerField, type RangeValue } from './dateRangePickerField'

export default function DateRangePicker() {
  const [range, setRange] = useState<RangeValue<CalendarDate> | null>({
    start: parseDate('2026-05-04'),
    end: parseDate('2026-05-10'),
  })

  return <DateRangePickerField value={range} onChange={setRange} />
}
