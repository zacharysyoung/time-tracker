import datetime
import unittest
import StringIO

import io_txt
from company_jobs import CompanyJobs
from invoice import Invoice
from time_entry import TimeEntry

_dt = datetime.datetime

class BaseClass(unittest.TestCase):
    def setUp(self):
        comp1 = 'Company1'
        comp2 = 'Company2'
        job1 = 'job1'
        job2 = 'job2'
        job3 = 'job3'
        job4 = 'job4'

        _te = TimeEntry
        self.entries = [
            _te(1.0, _dt(2010,1,1), '1st entry', comp1, job1),
            _te(2.0, _dt(2010,1,2), '2nd entry', comp1, job2),
            _te(2.5, _dt(2019,1,3), '3rd entry', comp2, job3, billable=False),
            _te(3.0, _dt(2019,2,4), '4th entry', comp2, job4)
        ]

        self.company1_jobs_dict = {job1: 'Job One', job2: 'Job Two'}
        self.company1_jobs = CompanyJobs(comp1, self.company1_jobs_dict, 20)

        self.company2_jobs_dict = {job3: 'Job Three', job4: 'Job Four'}
        self.company2_jobs = CompanyJobs(comp2, self.company2_jobs_dict, 20)
        
class TestTimeEntries(BaseClass):
    def testCreateTimeEntry(self):
        entry = TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1')

        self.assertEqual(entry.hours, 1.0)
        self.assertEqual(entry.dt, _dt(2010,1,1))
        self.assertEqual(entry.message, '1st entry')
        self.assertEqual(entry.company, 'Company1')
        self.assertEqual(entry.job, 'job1')

    def testSumEntryHours(self):
        entry1 = TimeEntry(1, None, None, None, None)
        entry2 = TimeEntry(2, None, None, None, None)
        entry3 = TimeEntry(2.5, None, None, None, None)
        entry4 = TimeEntry(3.0, None, None, None, None)

        _total = TimeEntry.get_hours_total
        self.assertEqual(_total([entry1, entry2]), 3.0)
        self.assertEqual(_total([entry1, entry2, entry3]), 5.5)
        self.assertEqual(_total([entry1, entry2, entry3, entry4]), 8.5)

    def testFilterEntries(self):
        comp1_entries = [
            TimeEntry(None, None, None, 'Company1', None) for i in range(100)
            ]
        comp2_entries = [
            TimeEntry(None, None, None, 'Company2', None) for i in range(100)
            ]
        comp3_entries = [
            TimeEntry(None, None, None, 'Company3', None) for i in range(100)
            ]

        all_entries = comp1_entries + comp2_entries + comp3_entries

        self.assertEqual(
            TimeEntry.query(all_entries, 'Company1'), comp1_entries)
        self.assertEqual(
            TimeEntry.query(all_entries, 'Company2'), comp2_entries)
        self.assertEqual(
            TimeEntry.query(all_entries, 'Company3'), comp3_entries)

        import random
        random.shuffle(all_entries)

        self.assertEqual(
            TimeEntry.query(all_entries, 'Company1'), comp1_entries)
        self.assertEqual(
            TimeEntry.query(all_entries, 'Company2'), comp2_entries)
        self.assertEqual(
            TimeEntry.query(all_entries, 'Company3'), comp3_entries)


class TestInvoicing(BaseClass):
    def testCreateInvoice(self):
        filtered_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(filtered_entries, None, (None, None), self.company1_jobs)
        self.assertEqual(invoice.hours_total, 3)

        filtered_entries = TimeEntry.query(self.entries, 'Company2')
        invoice = Invoice(filtered_entries, None, (None, None), self.company2_jobs)
        self.assertEqual(invoice.hours_total, 3)

    def testInvoicePayperiod(self):
        invoice = Invoice([],
                          _dt(2019,2,18),
                          (_dt(2019,2,4), _dt(2019,2,17)), self.company1_jobs)

        self.assertEqual(invoice.payperiod_start, _dt(2019,2,4))
        self.assertEqual(invoice.payperiod_end, _dt(2019,2,17))

        invoice = Invoice([],
                          None,
                          (_dt(2019,2,1), _dt(2019,2,28)), self.company1_jobs)
        self.assertEqual(invoice.payperiod_start, _dt(2019,2,1))
        self.assertEqual(invoice.payperiod_end, _dt(2019,2,28))

    def testSendInvoice(self):
        """Asserting the invoiced_dt value is weird, like what am I
           trying to prove?  So far, it's only use is being printed in
           text; of interest for future record keeping?  I don't
           really have a personal need for send(), so it's just this
           kinda-academic thing I thought an invoice should have.  And
           I think that uncertainty shows in this lame test.

        """
        
        filtered_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(filtered_entries, None, (None, None), self.company1_jobs)

        send_start = _dt.now()
        invoice.send()
        send_end = _dt.now()

        self.assertLess(send_start, invoice.invoiced_dt)
        self.assertGreater(send_end, invoice.invoiced_dt)

        for entry in invoice.entries:
            self.assertFalse(entry.can_be_invoiced())
            self.assertEqual(entry.invoiced_dt, invoice.invoiced_dt)

        self.assertTrue(invoice.sent)
        
class TestCompanyJobs(unittest.TestCase):
    def testCompanyJobs(self):
        company1_jobs_dict = {
            'job1': 'Job One',
            'job2': 'Job Two'
        }
        jobs = CompanyJobs('Company1', company1_jobs_dict, 20)

        self.assertEqual(jobs.wage, 20)
        
        # Test simple id <--> name
        self.assertEqual(jobs.get_id_by_name('Job One'), 'job1')
        self.assertEqual(jobs.get_name_by_id('job1'), 'Job One')
        self.assertEqual(jobs.get_id_by_name('Job Two'), 'job2')
        self.assertEqual(jobs.get_name_by_id('job2'), 'Job Two')

        # Test normalization
        self.assertEqual(jobs.get_id_by_name('job one'), 'job1')
        self.assertEqual(jobs.get_id_by_name('JoB One'), 'job1')
        self.assertEqual(jobs.get_id_by_name('JOB ONE'), 'job1')

        # id is not normalized
        self.assertIsNone(jobs.get_name_by_id('JOB1'))

        # Check for bogus name
        self.assertIsNone(jobs.get_id_by_name('Job 1'))


class TestGenInvoiceTask(unittest.TestCase):
    def testTaskWithMockData(self):
        import gen_invoice_task
        company1_jobs_dict = {'job1': 'Job One', 'job2': 'Job Two'}

        note_txt = """1,02/01/19,"Made an entry",Company1,Job One
2,2/2/19,Made another entry,Company1,Job Two"""

        invoice_txt = """Company1
Job One:
Fr 02/01/19: 1
----
total: 1

Job Two:
Sa 02/02/19: 2
----
total: 2

----
total: 3

"""

        invoice = gen_invoice_task.gen_invoice_task(
            ('Company1', _dt(2019,2,18,17,0),
             (_dt(2019,2,3), _dt(2019,2,17)), 20),
            company1_jobs_dict,
            StringIO.StringIO(note_txt)
        )
        self.assertEqual(io_txt.print_hours_for_ken(invoice), invoice_txt)


class TestFileOperations(unittest.TestCase):
    def testAppendFile(self):
        import os
        import tempfile

        import file_util

        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmpfile.close()

        tmpname = tmpfile.name

        with open(tmpname, 'w+b') as f:
            f.write('Old Line\n')

        file_util.append_file_with_data(tmpname, 'New Line\n')

        with open(tmpname, 'r+b') as f:
            self.assertEqual(f.read(), 'Old Line\nNew Line\n')

        file_util.del_path(tmpname)


    def testDeletePath(self):
        import os
        import tempfile

        import file_util

        # Test invalid deletes after system deletes file on f.close()
        f = tempfile.NamedTemporaryFile(delete=True)
        f.close()
        invalid_path = f.name
        with self.assertRaises(OSError):
            file_util.del_path(invalid_path)

        self.assertIsNone(file_util.del_path(invalid_path, ignore_error=2))
        
        # Test real delete; system does not delete on close: delete=False
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        self.assertTrue(os.path.exists(f.name))
        file_util.del_path(f.name)
        self.assertFalse(os.path.exists(f.name))
        

class TestIO(BaseClass):
    def testWriteInvoiceForTextingToKen(self):
        import io_txt
        invoice = Invoice(
            [TimeEntry(1, _dt(2010,1,1), None, 'Comp1', 'job1'),
             TimeEntry(2.5, _dt(2010,1,2), None, 'Comp1', 'job1')
             ],
            None,
            (_dt(2010,1,1), _dt(2010,1,13)),
            CompanyJobs('Comp1', {'job1': 'Job One'}, None)
        )
        txt = io_txt.print_hours_for_ken(invoice)
        self.assertEqual(
            txt,
            """Comp1
Job One:
Fr 01/01/10: 1
Sa 01/02/10: 2.5
----
total: 3.5

----
total: 3.5

"""
        )

    def testWriteInvoice(self):
        import tempfile
        import file_util

        comp1_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(comp1_entries, None, (None, None), self.company1_jobs)
        invoice.send()

        # open named-temp file to get its path
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmppath = tmpfile.name

        # close...
        tmpfile.close()

        # so other processes can open it
        io_txt.write_invoice_report(invoice, tmppath)

        entries_str = ''
        for entry in comp1_entries:
            entries_str += str(entry) + '\n'

        # Assert file was written and contains some basic values
        with open(tmppath, 'r') as f:
            written_txt =  f.read()
            self.assertIn(comp1_entries[0].message, written_txt)
            self.assertIn(
                str(TimeEntry.get_hours_total(comp1_entries)), written_txt)

        file_util.del_path(tmppath)
        
    def testPrintInvoicedEntries(self):
        entries = [
            TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1'),
            TimeEntry(2, _dt(2010,1,2), '2nd entry', 'Company1', 'job1'),
            TimeEntry(3, _dt(2010,1,3), '3rd entry', 'Company1', 'job1')
            ]
        invoice = Invoice(entries, _dt(2010,1,5,17,0), (None, None), self.company1_jobs)
        invoice.send()

        printed_txt = """| 1 | 01/01/10 | 1st entry | Company1 | job1 |
| 2 | 01/02/10 | 2nd entry | Company1 | job1 |
| 3 | 01/03/10 | 3rd entry | Company1 | job1 |

Total: 6 | Invoiced: {} | Payment due: 2010-01-05 17:00:00 | Gross $: 120
----
""".format(invoice.invoiced_dt)
        
        self.assertEqual(
            io_txt.print_entries(invoice).splitlines(),
            printed_txt.strip().splitlines()
        )

    def testParseEntryNote(self):
        def _test_parse(txt):
            parsed_entries = io_txt.parse_entries_from_note(
                StringIO.StringIO(txt), jobs
            )
            self.assertEqual(parsed_entries[0], entry)

        jobs = CompanyJobs('Company1', {'job1': 'Job One', 'job2': 'Job Two'}, 20)
        entry = TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1')

        # test m/d/yy
        _test_parse('1,1/1/10,1st entry,Company1,Job One')

        # test mm/dd/yy
        _test_parse('1,01/01/10,1st entry,Company1,Job One')

        # test job1 <--> Job One
        _test_parse('1,1/1/10,1st entry,Company1,job1')

        # test quoted comment
        _test_parse('1,1/1/10,"1st entry",Company1,job1')

        # test float
        _test_parse('1.0,1/1/10,"1st entry",Company1,job1')

        # errors
        with self.assertRaises(IndexError):
            _test_parse('')
