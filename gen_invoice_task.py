#! /usr/bin/env python

import datetime
import ConfigParser

from job_config import JobConfig
from invoice import Invoice
from time_entry import TimeEntry

def main(print_txt=True):
    company = 'cch'
    config = ConfigParser.ConfigParser()
    config_dict = config.readfp(open('jobs.ini', 'r'))
    jobs_dict = dict(config.items(company))
    note_data = open('note.txt', 'r')
    invoice = gen_invoice_task(company, jobs_dict, note_data)
    invoice.write_file('cch_invoice.txt')    

def gen_invoice_task(company, jobs_dict, note_data):
        cch_config = JobConfig(jobs_dict, company)

        entries = TimeEntry.parse_note(note_data, cch_config)
        entries = TimeEntry.query(entries, company)

        invoice = Invoice(
            entries,
            datetime.datetime(2019,2,18),
            config=cch_config)

        return invoice

if __name__ == '__main__':
    main()
