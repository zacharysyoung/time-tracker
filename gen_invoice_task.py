#! /usr/bin/env python

import datetime

from job_config import JobConfig
from invoice import Invoice
from time_entry import TimeEntry

def main(print_txt=True):
    config_data = open('jobs.ini', 'r')
    note_data = open('note.txt', 'r')
    invoice = gen_invoice_task('cch', config_data, note_data)
    invoice.write_file('cch_invoice.txt')    

def gen_invoice_task(company, config_data, note_data):
        cch_config = JobConfig(config_data, company)

        entries = TimeEntry.parse_note(note_data, cch_config)
        entries = TimeEntry.query(entries, company)

        invoice = Invoice(
            entries,
            datetime.datetime(2019,2,18),
            config=cch_config)

        return invoice

if __name__ == '__main__':
    main()
