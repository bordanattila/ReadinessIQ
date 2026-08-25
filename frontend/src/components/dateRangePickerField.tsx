import type { CalendarDate } from '@internationalized/date'
import {
  Button,
  CalendarCell,
  CalendarGrid,
  CalendarGridBody,
  CalendarGridHeader,
  CalendarHeaderCell,
  DateInput,
  DateRangePicker as AriaDateRangePicker,
  DateSegment,
  Dialog,
  Group,
  Heading,
  Label,
  Popover,
  RangeCalendar,
  type DateRangePickerProps,
} from 'react-aria-components'
import './dateRangePicker.theme.css'

export type { RangeValue } from 'react-aria-components'

export function DateRangePickerField(
  props: DateRangePickerProps<CalendarDate>,
) {
  return (
    <div className="riq-date-range-picker">
      <AriaDateRangePicker {...props}>
        <Label>Date range</Label>
        <Group>
          <div className="date-fields">
            <DateInput slot="start">
              {(segment) => <DateSegment segment={segment} />}
            </DateInput>
            <span aria-hidden="true" className="range-separator">
              –
            </span>
            <DateInput slot="end">
              {(segment) => <DateSegment segment={segment} />}
            </DateInput>
          </div>
          <Button className="field-Button" aria-label="Open calendar">
            ▾
          </Button>
        </Group>
        <Popover className="riq-date-range-popover">
          <Dialog>
            <RangeCalendar>
              <header>
                <Button slot="previous" aria-label="Previous month">
                  ◀
                </Button>
                <Heading />
                <Button slot="next" aria-label="Next month">
                  ▶
                </Button>
              </header>
              <CalendarGrid>
                <CalendarGridHeader>
                  {(day) => <CalendarHeaderCell>{day}</CalendarHeaderCell>}
                </CalendarGridHeader>
                <CalendarGridBody>
                  {(date) => <CalendarCell date={date} />}
                </CalendarGridBody>
              </CalendarGrid>
            </RangeCalendar>
          </Dialog>
        </Popover>
      </AriaDateRangePicker>
    </div>
  )
}
