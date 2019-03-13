import datetime
import unittest

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
            _te(4.9, _dt(2019,2,4), '4th entry', comp2, job4)
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

        for entry in TimeEntry.query(all_entries, 'Company1'):
            self.assertEqual(entry.company, 'Company1')
        for entry in TimeEntry.query(all_entries, 'Company2'):
            self.assertEqual(entry.company, 'Company2')
        for entry in TimeEntry.query(all_entries, 'Company3'):
            self.assertEqual(entry.company, 'Company3')

        import random
        random.shuffle(all_entries)

        for entry in TimeEntry.query(all_entries, 'Company1'):
            self.assertEqual(entry.company, 'Company1')
        for entry in TimeEntry.query(all_entries, 'Company2'):
            self.assertEqual(entry.company, 'Company2')
        for entry in TimeEntry.query(all_entries, 'Company3'):
            self.assertEqual(entry.company, 'Company3')

    def testFilterEntriesByDate(self):
        e1 = TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1')
        e2 = TimeEntry(1, _dt(2010,1,2), '2nd entry', 'Company1', 'job1')
        e3 = TimeEntry(1, _dt(2010,1,3), '3rd entry', 'Company1', 'job1')

        self.assertEqual(
            TimeEntry.filter_by_date([e1], _dt(2010,1,1), _dt(2010,1,1)),
            [e1]
            )

        self.assertEqual(
            TimeEntry.filter_by_date([e1, e2, e3], _dt(2010,1,1), _dt(2010,1,1)),
            [e1]
            )

        # With date range in February, all January entries are filtered out
        self.assertEqual(
            TimeEntry.filter_by_date([e1, e2, e3], _dt(2010,2,1), _dt(2010,2,3)),
            []
            )

class TestInvoicing(BaseClass):
    def testCreateInvoice(self):
        filtered_entries = TimeEntry.query(self.entries, 'Company1')
        invoice = Invoice(filtered_entries, None, (None, None), self.company1_jobs)
        self.assertEqual(invoice.hours_total, 3)

        filtered_entries = TimeEntry.query(self.entries, 'Company2')
        invoice = Invoice(filtered_entries, None, (None, None), self.company2_jobs)
        self.assertEqual(invoice.hours_total, 4.9)

        filtered_entry_ids = [e.id for e in filtered_entries]
        self.assertEqual(sorted(invoice.entry_ids), sorted(filtered_entry_ids))

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

    def testIdCollisions(self):
        """Using something other than self(id), right now uuid1().

           I was using self.id = id(self) for ID, which would make for
           a collison in about 10 iterations of the following loop.
           Noticed this problem as an intermittent
           already-exists-error in:

             test_io:TestGenInvoice.testRealRun()

        """
        ids = []
        for i in range(100):
            invoice = Invoice(
            [
                TimeEntry(1, _dt(2010,1,1), '1st entry', 'Company1', 'job1'),
                TimeEntry(2.5, _dt(2010,1,2), '2nd entry', 'Company1', 'job1')
            ],
            _dt(2010,1,14),
            (_dt(2010,1,1), _dt(2010,1,13)),
            CompanyJobs('Company1', {'job1': 'Job One'}, 20)
            )
            self.assertNotIn(invoice.id, ids)
            ids.append(invoice.id)


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
