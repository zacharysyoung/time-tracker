import datetime

from collections import defaultdict

from time_entry import TimeEntry

class Invoice(object):
    def __init__(self, entries, payment_dt, pay_period, jobs):
        self.company = jobs.company

        for i in range(len(entries) - 1, -1, -1):
            if entries[i].company != self.company:
                raise ValueError(
                    'Entry with different company: %s and %s' % (
                        repr(entries[i]), self.company))

            if not entries[i].can_be_invoiced():
                del(entries[i])

        self.entries = sorted(entries, key=lambda x: x.dt)
        self.job_ids = defaultdict(list)
        for entry in self.entries:
            self.job_ids[entry.job].append(entry)

        self.hours_total  = TimeEntry.get_hours_total(self.entries)
        self.invoiced_dt = None
        self.payment_dt = payment_dt
        self.paid_dt = None
        self.sent = False

        self.payperiod_start = pay_period[0]
        self.payperiod_end = pay_period[1]
        self.jobs = jobs

    def __eq__(self, other):
        return self.company == other.company and \
            self.entries == other.entries and \
            self.hours_total == other.hours_total and \
            self.invoiced_dt == other.invoiced_dt and \
            self.payment_dt == other.payment_dt and \
            self.paid_dt == other.paid_dt and \
            self.sent == other.sent and \
            self.payperiod_start == other.payperiod_start and \
            self.payperiod_end == other.payperiod_end and \
            self.jobs == other.jobs
    

    def send(self):
        now = datetime.datetime.now()
        total = 0
        for entry in self.entries:
            entry.invoiced = True
            entry.invoiced_dt = now
            total += entry.hours
        self.invoiced_dt = now
        self.sent = True
        self.total_hours = total
