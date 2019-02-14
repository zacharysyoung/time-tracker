import tempfile
import unittest

import file_util

from io_text import IoTxt

class TestCompanyJobs(unittest.TestCase):
    def testReader(self):
        tmpfile = tempfile.NamedTemporaryFile(delete=False)

        tmpfile.write('[Company1]\n')
        tmpfile.write('job1: Job One\n')
        tmpfile.write('job2: Job Two\n')
        
        # close...
        tmppath = tmpfile.name
        tmpfile.close()

        jobs_dict = IoTxt.read_company_jobs(tmppath, 'Company1')
        self.assertEqual(jobs_dict, {'job1': 'Job One', 'job2': 'Job Two'})

        file_util.del_path(tmppath)

class TestInvoice(unittest.TestCase):
    def testWriter(self):
        from datetime import datetime as _dt
        from company_jobs import CompanyJobs
        from invoice import Invoice
        from time_entry import TimeEntry

        invoice = Invoice(
            [TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1')],
            _dt(2010,1,14),
            (_dt(2010,1,1), _dt(2010,1,13)),
            CompanyJobs('Company1', {'job1': 'Job One'}, 20)
        )
        invoice.send()

        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmppath = tmpfile.name
        tmpfile.close()
        
        IoTxt.write_invoice(tmppath, invoice)

        invoice_txt = """Company1
Job One:
Fr 01/01/10: 1
----
total: 1

----
total: 1

| 1 | 01/01/10 | 1st entry | Company1 | job1 |

Total: 1 | Invoiced: {} | Payment due: 2010-01-14 00:00:00 | Gross $: 20
----
""".format(invoice.invoiced_dt)
    
        with open(tmppath, 'r') as f:
            self.assertEqual(f.read().splitlines(), invoice_txt.splitlines())
        
        file_util.del_path(tmppath)
