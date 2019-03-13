#! /usr/bin/env python

import datetime
import ConfigParser

import io_txt
from company_jobs import CompanyJobs
from invoice import Invoice
from time_entry import TimeEntry

_dt = datetime.datetime

ff = ('ff', _dt(2019,3,1, 17, 0), (_dt(2019,2,1), _dt(2019,2,28)), 0)
cch = ('cch', _dt(2019,3,4, 17, 0), (_dt(2019,2,18), _dt(2019,3,3)), 20)

def main(company, print_txt=True):
    config = ConfigParser.ConfigParser()
    config.readfp(open('jobs.ini', 'r'))
    jobs_dict = dict(config.items(company[0]))
    note_data = open('note.txt', 'r')
    invoice = gen_invoice_task(company, jobs_dict, note_data)
    invoice.send()

    invoice_path = io_txt.get_invoice_path(invoice)
    report_path = io_txt.get_report_path(invoice)
    io_txt.write_invoice(invoice)
    io_txt.write_report(invoice)

    return invoice_path, report_path

def gen_invoice_task(company, jobs_dict, note_data):
    company_name, payment_dt, pay_period, wage = company
    jobs = CompanyJobs(company[0], jobs_dict, wage)

    entries = io_txt.parse_entries_from_note(note_data, jobs)
    entries = TimeEntry.query(entries, company[0])
    entries = TimeEntry.filter_by_date(entries, *pay_period)

    invoice = Invoice(
        entries,
        company[1],
        company[2],
        jobs)

    return invoice

if __name__ == '__main__':
    main(ff)
