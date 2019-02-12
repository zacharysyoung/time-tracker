#! /usr/bin/env python

import datetime
import ConfigParser

from company_jobs import CompanyJobs
from invoice import Invoice
from time_entry import TimeEntry

def main(print_txt=True):
    company = 'cch'
    config = ConfigParser.ConfigParser()
    config.readfp(open('jobs.ini', 'r'))
    jobs_dict = dict(config.items(company))
    note_data = open('note.txt', 'r')
    invoice = gen_invoice_task(company, jobs_dict, note_data)
    invoice.write_file('cch_invoice.txt')    

def gen_invoice_task(company, jobs_dict, note_data):
        jobs = CompanyJobs(company, jobs_dict)

        entries = TimeEntry.parse_note(note_data, jobs)
        entries = TimeEntry.query(entries, company)

        invoice = Invoice(
            entries,
            datetime.datetime(2019,2,18),
            jobs=jobs)

        return invoice

if __name__ == '__main__':
    main()
