#! /usr/bin/env python

import datetime
import ConfigParser

from company_jobs import CompanyJobs
from invoice import Invoice
from time_entry import TimeEntry

_dt = datetime.datetime

ff = ('ff', _dt(2019,3,1, 17, 0), (_dt(2019,2,1), _dt(2019,2,28)))
cch = ('cch', _dt(2019,3,4, 17, 0), (_dt(2019,2,18), _dt(2019,3,3)))

def main(company, print_txt=True):
    config = ConfigParser.ConfigParser()
    config.readfp(open('jobs.ini', 'r'))
    jobs_dict = dict(config.items(company[0]))
    note_data = open('note.txt', 'r')
    invoice = gen_invoice_task(company, jobs_dict, note_data)
    invoice.send()

    fname = 'invoices/{:%Y%m%d}_{:%Y%m%d}_{}.txt'.format(invoice.payperiod_start, invoice.payperiod_end, company[0])
    invoice.write_file(fname)    

def gen_invoice_task(company, jobs_dict, note_data):
        jobs = CompanyJobs(company[0], jobs_dict)

        entries = TimeEntry.parse_note(note_data, jobs)
        entries = TimeEntry.query(entries, company[0])

        invoice = Invoice(
            entries,
            company[1],
            company[2],
            jobs)

        return invoice

if __name__ == '__main__':
    main(ff)
